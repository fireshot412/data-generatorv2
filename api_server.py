#!/usr/bin/env python3
"""
Flask API Server for Continuous Data Generator.
Provides REST API for the HTML UI to interact with continuous generation services.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import asyncio
import threading
from typing import Dict, Optional
import json

from continuous.state_manager import StateManager
from continuous.llm_generator import LLMGenerator
from continuous.connections.asana_connection import AsanaClientPool
from continuous.connections.okta_connection import OktaClientPool
from continuous.connections.salesforce_connection import SalesforceClientPool
from continuous.services.asana_service import AsanaService, ContinuousService
from continuous.services.okta_service import OktaService
from continuous.services.salesforce_service import SalesforceService

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

# Global state
state_manager = StateManager(".")
running_services: Dict[str, ContinuousService] = {}
service_threads: Dict[str, threading.Thread] = {}


def run_service_in_thread(service: ContinuousService):
    """Run async service in a thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        print(f"[Thread] Starting service.run() for job {service.job_id}")
        loop.run_until_complete(service.run())
        print(f"[Thread] Service.run() completed for job {service.job_id}")
    except Exception as e:
        import traceback
        print(f"[Thread] EXCEPTION in service.run() for job {service.job_id}:")
        print(f"[Thread] {type(e).__name__}: {e}")
        traceback.print_exc()
    finally:
        loop.close()


def restart_running_jobs():
    """Restart jobs that were running when server last stopped."""
    print("\n" + "=" * 60)
    print("Checking for jobs to restart...")
    print("=" * 60)

    try:
        jobs = state_manager.get_all_jobs()
        restarted_count = 0

        for job_summary in jobs:
            # Only restart jobs that were running or paused - DO NOT restart stopped jobs
            if job_summary['status'] in ['running', 'paused']:
                job_id = job_summary['job_id']

                # Load full job state
                state = state_manager.load_state(job_id)
                if not state:
                    continue

                # Skip jobs marked for deletion
                if state.get("_deleting"):
                    print(f"⏭ Skipping job {job_id}: Marked for deletion")
                    continue

                config = state.get('config', {})
                connection_type = state.get('connection_type', 'asana')

                # Recreate the service components
                try:
                    llm_generator = LLMGenerator(config.get('anthropic_api_key', ''))

                    # Route based on connection type
                    if connection_type == 'asana':
                        # Parse user tokens for Asana
                        user_tokens = {}
                        for user_data in config['user_tokens']:
                            user_tokens[user_data['name']] = user_data['token']

                        client_pool = AsanaClientPool(user_tokens)

                        if len(client_pool.get_valid_clients()) == 0:
                            print(f"⚠ Skipping job {job_id}: No valid Asana API tokens")
                            continue

                        # Create Asana service with existing job_id
                        service = ContinuousService.__new__(ContinuousService)
                        service.config = config
                        service.state_manager = state_manager
                        service.llm = llm_generator
                        service.client_pool = client_pool
                        service.scheduler = __import__('continuous.scheduler', fromlist=['ActivityScheduler']).ActivityScheduler(config)
                        service.job_id = job_id
                        service.state = state
                        service.running = False
                        service.paused = (job_summary['status'] in ['paused', 'stopped'])
                        service.deleted = False  # Initialize deleted flag

                    elif connection_type == 'okta':
                        # Create Okta client pool
                        okta_pool = OktaClientPool(config['user_tokens'])

                        if len(okta_pool.get_valid_clients()) == 0:
                            print(f"⚠ Skipping job {job_id}: No valid Okta API tokens")
                            continue

                        # Create Okta service
                        service = OktaService(config, state_manager, llm_generator, okta_pool)
                        service.job_id = job_id
                        service.state = state
                        service.running = False
                        service.paused = (job_summary['status'] in ['paused', 'stopped'])
                        service.deleted = False

                    elif connection_type == 'salesforce':
                        # Create Salesforce client pool
                        sf_pool = SalesforceClientPool(config['user_tokens'])

                        if len(sf_pool.get_valid_clients()) == 0:
                            print(f"⚠ Skipping job {job_id}: No valid Salesforce credentials")
                            continue

                        # Create Salesforce service
                        service = SalesforceService(config, state_manager, llm_generator, sf_pool)
                        service.job_id = job_id
                        service.state = state
                        service.running = False
                        service.paused = (job_summary['status'] in ['paused', 'stopped'])
                        service.deleted = False

                    else:
                        print(f"⚠ Skipping job {job_id}: Unsupported connection type '{connection_type}'")
                        continue

                    # Start service in background thread
                    thread = threading.Thread(target=run_service_in_thread, args=(service,), daemon=True)
                    thread.start()

                    # Store references
                    running_services[job_id] = service
                    service_threads[job_id] = thread

                    status_emoji = "⏸" if service.paused else "▶️"
                    print(f"{status_emoji} Restarted {connection_type} job {job_id} ({config.get('industry', 'unknown')})")
                    restarted_count += 1

                except Exception as e:
                    print(f"✗ Error restarting job {job_id}: {e}")

        if restarted_count > 0:
            print(f"\n✓ Successfully restarted {restarted_count} job(s)")
        else:
            print("No jobs to restart")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"✗ Error checking for jobs to restart: {e}")
        print("=" * 60 + "\n")


@app.route('/')
def index():
    """Serve the marketing landing page."""
    return send_from_directory('.', 'marketing.html')

@app.route('/dashboard')
def dashboard():
    """Serve the Asana Data Generator dashboard."""
    response = send_from_directory('.', 'dashboard.html')
    # Prevent browser caching to ensure updates are loaded
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/old')
def old_ui():
    """Serve the old HTML UI."""
    return send_from_directory('.', 'asana_project_creator.html')

@app.route('/marketing-styles.css')
def marketing_styles():
    """Serve marketing styles."""
    return send_from_directory('.', 'marketing-styles.css')

@app.route('/marketing-script.js')
def marketing_script():
    """Serve marketing script."""
    return send_from_directory('.', 'marketing-script.js')


@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get list of all jobs."""
    try:
        jobs = state_manager.get_all_jobs()
        return jsonify({
            "success": True,
            "jobs": jobs
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get detailed information about a specific job."""
    try:
        state = state_manager.load_state(job_id)
        if not state:
            return jsonify({
                "success": False,
                "error": "Job not found"
            }), 404

        return jsonify({
            "success": True,
            "job": state
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/jobs/<job_id>/activity_log', methods=['GET'])
def get_activity_log(job_id):
    """Get activity log for a job."""
    try:
        state = state_manager.load_state(job_id)
        if not state:
            return jsonify({
                "success": False,
                "error": "Job not found"
            }), 404

        # Get pagination parameters
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        activity_log = state.get("activity_log", [])

        # Reverse so newest first
        activity_log = list(reversed(activity_log))

        # Paginate
        paginated = activity_log[offset:offset + limit]

        return jsonify({
            "success": True,
            "activities": paginated,
            "total": len(activity_log),
            "offset": offset,
            "limit": limit
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/jobs/start', methods=['POST'])
def start_job():
    """Start a new continuous generation job (supports Asana and Okta)."""
    try:
        config = request.json
        connection_type = config.get('connection_type', 'asana')

        # Validate connection-specific required fields
        if connection_type == 'asana':
            required = ['industry', 'workspace_gid', 'user_tokens', 'anthropic_api_key']
            for field in required:
                if field not in config:
                    return jsonify({
                        "success": False,
                        "error": f"Missing required field for Asana: {field}"
                    }), 400

            # Initialize components
            llm_generator = LLMGenerator(config['anthropic_api_key'])

            # Parse user tokens
            user_tokens = {}
            for user_data in config['user_tokens']:
                user_tokens[user_data['name']] = user_data['token']

            client_pool = AsanaClientPool(user_tokens)

            # Validate at least one valid client
            if len(client_pool.get_valid_clients()) == 0:
                return jsonify({
                    "success": False,
                    "error": "No valid Asana API tokens provided"
                }), 400

            # Create service
            service = ContinuousService(config, state_manager, llm_generator, client_pool)
            job_id = service.job_id

        elif connection_type == 'okta':
            required = ['industry', 'org_url', 'user_tokens', 'org_size', 'anthropic_api_key']
            for field in required:
                if field not in config:
                    return jsonify({
                        "success": False,
                        "error": f"Missing required field for Okta: {field}"
                    }), 400

            # Validate org_url format
            if not config['org_url'].startswith('https://'):
                return jsonify({
                    "success": False,
                    "error": "org_url must start with https://"
                }), 400

            # Validate user_tokens have org_url
            for token in config['user_tokens']:
                if 'org_url' not in token:
                    return jsonify({
                        "success": False,
                        "error": "Each user token must include org_url for Okta"
                    }), 400

            # Initialize components
            llm_generator = LLMGenerator(config['anthropic_api_key'])

            # Create Okta client pool
            okta_pool = OktaClientPool(config['user_tokens'])

            # Validate at least one valid client
            if len(okta_pool.get_valid_clients()) == 0:
                return jsonify({
                    "success": False,
                    "error": "No valid Okta API tokens provided"
                }), 400

            # Create Okta service
            service = OktaService(config, state_manager, llm_generator, okta_pool)
            job_id = service.job_id

        elif connection_type == 'salesforce':
            required = ['industry', 'instance_url', 'user_tokens', 'org_size', 'anthropic_api_key']
            for field in required:
                if field not in config:
                    return jsonify({
                        "success": False,
                        "error": f"Missing required field for Salesforce: {field}"
                    }), 400

            # Validate instance_url format
            if not config['instance_url'].startswith('https://'):
                return jsonify({
                    "success": False,
                    "error": "instance_url must start with https://"
                }), 400

            # Validate and parse user tokens
            user_credentials = {}
            for user_data in config['user_tokens']:
                if not all(k in user_data for k in ['name', 'username', 'password', 'security_token', 'instance_url']):
                    return jsonify({
                        "success": False,
                        "error": "Each user token must include name, username, password, security_token, and instance_url for Salesforce"
                    }), 400

                # Parse into format expected by SalesforceClientPool
                user_credentials[user_data['name']] = {
                    'username': user_data['username'],
                    'password': user_data['password'],
                    'security_token': user_data['security_token'],
                    'instance_url': user_data['instance_url']
                }

            # Initialize components
            llm_generator = LLMGenerator(config['anthropic_api_key'])

            # Create Salesforce client pool
            sf_pool = SalesforceClientPool(user_credentials)

            # Validate at least one valid client
            if len(sf_pool.get_valid_clients()) == 0:
                return jsonify({
                    "success": False,
                    "error": "No valid Salesforce credentials provided"
                }), 400

            # Create Salesforce service
            service = SalesforceService(config, state_manager, llm_generator, sf_pool)
            job_id = service.job_id

        else:
            return jsonify({
                "success": False,
                "error": f"Unsupported connection type: {connection_type}"
            }), 400

        # Start service in background thread
        thread = threading.Thread(target=run_service_in_thread, args=(service,), daemon=True)
        thread.start()

        # Store references
        running_services[job_id] = service
        service_threads[job_id] = thread

        return jsonify({
            "success": True,
            "job_id": job_id,
            "connection_type": connection_type,
            "message": f"{connection_type.capitalize()} continuous generation started - Job ID: {job_id}"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/jobs/<job_id>/stop', methods=['POST'])
def stop_job(job_id):
    """Stop a running job (pause it, keeping it resumable)."""
    try:
        if job_id in running_services:
            service = running_services[job_id]
            service.stop()

            # Keep service in running_services so it can be resumed
            # Don't remove from tracking - it's just paused

            return jsonify({
                "success": True,
                "message": f"Job {job_id} stopped"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Job not found or not running"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/jobs/<job_id>/pause', methods=['POST'])
def pause_job(job_id):
    """Pause a running job."""
    try:
        if job_id in running_services:
            service = running_services[job_id]
            service.pause()

            return jsonify({
                "success": True,
                "message": f"Job {job_id} paused"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Job not found or not running"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/jobs/<job_id>/resume', methods=['POST'])
def resume_job(job_id):
    """Resume a paused job."""
    try:
        if job_id in running_services:
            service = running_services[job_id]
            service.resume()

            return jsonify({
                "success": True,
                "message": f"Job {job_id} resumed"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Job not found or not running"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/jobs/<job_id>/generate-now', methods=['POST'])
def generate_now(job_id):
    """Generate activity immediately for this job."""
    try:
        if job_id in running_services:
            service = running_services[job_id]

            # Run activity generation in background thread
            import threading
            from datetime import datetime, timezone

            def run_generation():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(service._generate_activity())

                    # Update next activity time
                    current_time = datetime.now(timezone.utc)
                    next_time = service.scheduler.get_next_activity_time(current_time)
                    service.state_manager.update_next_activity_time(job_id, next_time.isoformat())
                finally:
                    loop.close()

            thread = threading.Thread(target=run_generation, daemon=True)
            thread.start()

            return jsonify({
                "success": True,
                "message": f"Activity generated for job {job_id}"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Job not found or not running"
            }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/jobs/<job_id>/cleanup', methods=['POST'])
def cleanup_job(job_id):
    """Clean up platform data for a job (supports Asana and Okta)."""
    try:
        # Load state to get service config
        state = state_manager.load_state(job_id)
        if not state:
            return jsonify({
                "success": False,
                "error": "Job not found"
            }), 404

        config = state.get('config', {})
        connection_type = state.get('connection_type', 'asana')

        # Re-create service components for cleanup
        llm_generator = LLMGenerator(config.get('anthropic_api_key', ''))

        # Route based on connection type
        if connection_type == 'asana':
            user_tokens = {}
            for user_data in config['user_tokens']:
                user_tokens[user_data['name']] = user_data['token']

            client_pool = AsanaClientPool(user_tokens)

            if len(client_pool.get_valid_clients()) == 0:
                return jsonify({
                    "success": False,
                    "error": "No valid Asana API tokens available for cleanup"
                }), 400

            # Create temporary service for cleanup
            service = ContinuousService.__new__(ContinuousService)
            service.config = config
            service.state_manager = state_manager
            service.llm = llm_generator
            service.client_pool = client_pool
            service.job_id = job_id
            service.state = state

            # Initialize workspace-level object caches (required for cleanup)
            service.workspace_custom_fields = {}
            service.workspace_tags = {}
            service.workspace_portfolios = {}

            # Run cleanup synchronously in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(service.cleanup_asana_data())
            finally:
                loop.close()

            return jsonify({
                "success": result["success"],
                "deleted_projects": result.get("deleted_projects", 0),
                "deleted_tasks": result.get("deleted_tasks", 0),
                "deleted_subtasks": result.get("deleted_subtasks", 0),
                "total_projects": result.get("total_projects", 0),
                "failed_projects": result.get("failed_projects", [])
            })

        elif connection_type == 'okta':
            # Create Okta client pool
            okta_pool = OktaClientPool(config['user_tokens'])

            if len(okta_pool.get_valid_clients()) == 0:
                return jsonify({
                    "success": False,
                    "error": "No valid Okta API tokens available for cleanup"
                }), 400

            # Create Okta service for cleanup
            service = OktaService(config, state_manager, llm_generator, okta_pool)
            service.job_id = job_id
            service.state = state

            # Run cleanup synchronously in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(service.cleanup_platform_data())
            finally:
                loop.close()

            return jsonify({
                "success": True,
                "users_deleted": result.get("users_deleted", 0),
                "groups_deleted": result.get("groups_deleted", 0),
                "assignments_removed": result.get("assignments_removed", 0),
                "errors": result.get("errors", [])
            })

        elif connection_type == 'salesforce':
            # Create Salesforce client pool
            sf_pool = SalesforceClientPool(config['user_tokens'])

            if len(sf_pool.get_valid_clients()) == 0:
                return jsonify({
                    "success": False,
                    "error": "No valid Salesforce credentials available for cleanup"
                }), 400

            # Create Salesforce service for cleanup
            service = SalesforceService(config, state_manager, llm_generator, sf_pool)
            service.job_id = job_id
            service.state = state

            # Run cleanup synchronously in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(service.cleanup_platform_data())
            finally:
                loop.close()

            return jsonify({
                "success": True,
                "campaigns_deleted": result.get("campaigns_deleted", 0),
                "opportunities_deleted": result.get("opportunities_deleted", 0),
                "cases_deleted": result.get("cases_deleted", 0),
                "contacts_deleted": result.get("contacts_deleted", 0),
                "accounts_deleted": result.get("accounts_deleted", 0),
                "leads_deleted": result.get("leads_deleted", 0),
                "errors": result.get("errors", [])
            })

        else:
            return jsonify({
                "success": False,
                "error": f"Unsupported connection type: {connection_type}"
            }), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/workspace/<workspace_gid>/cleanup', methods=['POST'])
def cleanup_workspace(workspace_gid):
    """
    NUCLEAR OPTION: Clean up ALL Asana data in a workspace (except users).
    Deletes everything with proper bottom-up traversal to avoid orphaned objects.
    """
    try:
        data = request.json
        user_tokens_data = data.get('user_tokens', [])

        if not user_tokens_data:
            return jsonify({
                "success": False,
                "error": "No user tokens provided"
            }), 400

        # Parse user tokens
        user_tokens = {}
        for user_data in user_tokens_data:
            user_tokens[user_data['name']] = user_data['token']

        client_pool = AsanaClientPool(user_tokens)
        all_clients = client_pool.get_valid_clients()

        if not all_clients:
            return jsonify({
                "success": False,
                "error": "No valid API tokens available for cleanup"
            }), 400

        # Helper function to try deletion with each client until one succeeds
        def try_delete_with_clients(delete_func, item_description: str) -> bool:
            """Try deletion with each available client until one succeeds."""
            for client in all_clients:
                try:
                    delete_func(client)
                    return True
                except Exception as e:
                    error_str = str(e)
                    # If it's a permission error (403), try next client
                    if "403" in error_str or "permission" in error_str.lower() or "Forbidden" in error_str:
                        continue
                    else:
                        # For non-permission errors, just try next client
                        continue
            return False

        # Run cleanup synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                cleanup_entire_workspace(workspace_gid, all_clients, try_delete_with_clients)
            )
        finally:
            loop.close()

        return jsonify(result)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


async def cleanup_entire_workspace(workspace_gid: str, all_clients, try_delete_with_clients):
    """
    Delete all objects in a workspace using proper bottom-up traversal.

    Deletion order:
    1. Subtasks (children of tasks)
    2. Tasks (children of projects)
    3. Projects (containers)
    4. Portfolios (workspace-level)
    5. Custom Fields (workspace-level)
    6. Tags (workspace-level)

    NOTE: This does NOT delete:
    - Users
    - Personal Access Tokens (PATs) - these cannot be deleted via API
    - Workspace settings
    """
    import asyncio

    print(f"\n{'='*60}")
    print(f"Starting WORKSPACE-LEVEL cleanup for workspace {workspace_gid}")
    print(f"WARNING: This will delete ALL workspace objects!")
    print(f"Protected: Users, Personal Access Tokens, Workspace Settings")
    print(f"{'='*60}\n")

    deleted_subtasks = 0
    deleted_tasks = 0
    deleted_projects = 0
    deleted_portfolios = 0
    deleted_custom_fields = 0
    deleted_tags = 0
    failed_items = []

    client = all_clients[0]  # Use first client for reading

    # Step 1: Get all projects in workspace (with pagination)
    print(f"  Fetching all projects in workspace...")
    try:
        projects = client.get_workspace_projects(workspace_gid)
        print(f"  Found {len(projects)} project(s)")
    except Exception as e:
        print(f"  ✗ Error fetching projects: {e}")
        projects = []

    # Step 2: For each project, delete subtasks → tasks → project
    for idx, project in enumerate(projects):
        project_gid = project.get("gid")
        project_name = project.get("name", "Unknown Project")

        print(f"\n  [{idx+1}/{len(projects)}] Processing project: {project_name}")

        try:
            # Get all tasks in project
            tasks = client.get_project_tasks(project_gid)
            print(f"    Found {len(tasks)} task(s)")

            # Delete each task and its subtasks
            for task in tasks:
                task_gid = task.get("gid")

                try:
                    # Get and delete subtasks first
                    subtasks = client.get_task_subtasks(task_gid)
                    for subtask in subtasks:
                        subtask_gid = subtask.get("gid")
                        if try_delete_with_clients(
                            lambda c: c.delete_task(subtask_gid),
                            f"subtask {subtask_gid}"
                        ):
                            deleted_subtasks += 1
                        await asyncio.sleep(0.1)

                    # Delete the task
                    if try_delete_with_clients(
                        lambda c: c.delete_task(task_gid),
                        f"task {task_gid}"
                    ):
                        deleted_tasks += 1
                    await asyncio.sleep(0.1)

                except Exception as e:
                    print(f"      ⚠ Error processing task {task_gid}: {e}")

        except Exception as e:
            print(f"    ⚠ Error fetching tasks for project: {e}")

        # Delete the project
        try:
            if try_delete_with_clients(
                lambda c: c.delete_project(project_gid),
                f"project {project_gid}"
            ):
                deleted_projects += 1
                print(f"    ✓ Deleted project: {project_name}")
            else:
                failed_items.append({
                    "type": "project",
                    "id": project_gid,
                    "name": project_name,
                    "error": "No client has permission"
                })
        except Exception as e:
            print(f"    ✗ Error deleting project: {e}")
            failed_items.append({
                "type": "project",
                "id": project_gid,
                "name": project_name,
                "error": str(e)
            })

        await asyncio.sleep(0.2)

    # Step 3: Delete orphaned tasks (tasks not in any project)
    print(f"\n  Checking for orphaned tasks...")
    try:
        users = client.get_workspace_users(workspace_gid)
        print(f"    Found {len(users)} user(s) to check")

        orphaned_task_count = 0
        for user in users:
            user_gid = user.get("gid")
            user_name = user.get("name", "Unknown User")

            try:
                # Get all tasks assigned to this user in the workspace
                user_tasks = client.get_user_tasks_in_workspace(workspace_gid, user_gid)

                if user_tasks:
                    print(f"    Found {len(user_tasks)} task(s) for {user_name}")

                    for task in user_tasks:
                        task_gid = task.get("gid")
                        task_name = task.get("name", "Unknown Task")

                        try:
                            # Try to delete the task
                            if try_delete_with_clients(
                                lambda c: c.delete_task(task_gid),
                                f"orphaned task {task_name}"
                            ):
                                orphaned_task_count += 1
                                deleted_tasks += 1
                                print(f"      ✓ Deleted orphaned task: {task_name}")
                            await asyncio.sleep(0.1)
                        except Exception as e:
                            print(f"      ⚠ Error deleting orphaned task {task_name}: {e}")

            except Exception as e:
                print(f"    ⚠ Error fetching tasks for user {user_name}: {e}")

        if orphaned_task_count > 0:
            print(f"    ✓ Deleted {orphaned_task_count} orphaned task(s)")
        else:
            print(f"    No orphaned tasks found")

    except Exception as e:
        print(f"    ⚠ Error processing orphaned tasks: {e}")

    # Step 4: Delete portfolios
    print(f"\n  Deleting portfolios...")
    try:
        # Collect portfolios from all users (since portfolios are owned by specific users)
        all_portfolios = {}  # Use dict to deduplicate by GID

        for user_client in all_clients:
            try:
                user_portfolios = user_client.get_workspace_portfolios(workspace_gid)
                for portfolio in user_portfolios:
                    portfolio_gid = portfolio.get("gid")
                    if portfolio_gid and portfolio_gid not in all_portfolios:
                        all_portfolios[portfolio_gid] = portfolio
            except Exception as e:
                print(f"    ⚠ Error fetching portfolios for one user: {e}")
                continue

        print(f"    Found {len(all_portfolios)} portfolio(s)")

        for portfolio_gid, portfolio in all_portfolios.items():
            portfolio_name = portfolio.get("name", "Unknown Portfolio")

            if try_delete_with_clients(
                lambda c: c.delete_portfolio(portfolio_gid),
                f"portfolio {portfolio_name}"
            ):
                deleted_portfolios += 1
                print(f"    ✓ Deleted portfolio: {portfolio_name}")
            await asyncio.sleep(0.1)

    except Exception as e:
        print(f"    ⚠ Error processing portfolios: {e}")

    # Step 5: Delete custom fields
    print(f"\n  Deleting custom fields...")
    try:
        custom_fields = client.get_workspace_custom_fields(workspace_gid)
        print(f"    Found {len(custom_fields)} custom field(s)")

        for field in custom_fields:
            field_gid = field.get("gid")
            field_name = field.get("name", "Unknown Field")

            if try_delete_with_clients(
                lambda c: c.delete_custom_field(field_gid),
                f"custom field {field_name}"
            ):
                deleted_custom_fields += 1
                print(f"    ✓ Deleted custom field: {field_name}")
            await asyncio.sleep(0.1)

    except Exception as e:
        print(f"    ⚠ Error processing custom fields: {e}")

    # Step 6: Delete tags
    print(f"\n  Deleting tags...")
    try:
        tags = client.get_workspace_tags(workspace_gid)
        print(f"    Found {len(tags)} tag(s)")

        for tag in tags:
            tag_gid = tag.get("gid")
            tag_name = tag.get("name", "Unknown Tag")

            if try_delete_with_clients(
                lambda c: c.delete_tag(tag_gid),
                f"tag {tag_name}"
            ):
                deleted_tags += 1
                print(f"    ✓ Deleted tag: {tag_name}")
            await asyncio.sleep(0.1)

    except Exception as e:
        print(f"    ⚠ Error processing tags: {e}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Workspace Cleanup Summary:")
    print(f"  Deleted subtasks: {deleted_subtasks}")
    print(f"  Deleted tasks: {deleted_tasks}")
    print(f"  Deleted projects: {deleted_projects}")
    print(f"  Deleted portfolios: {deleted_portfolios}")
    print(f"  Deleted custom fields: {deleted_custom_fields}")
    print(f"  Deleted tags: {deleted_tags}")
    print(f"  Failed items: {len(failed_items)}")
    print(f"{'='*60}\n")

    return {
        "success": len(failed_items) == 0,
        "deleted_subtasks": deleted_subtasks,
        "deleted_tasks": deleted_tasks,
        "deleted_projects": deleted_projects,
        "deleted_portfolios": deleted_portfolios,
        "deleted_custom_fields": deleted_custom_fields,
        "deleted_tags": deleted_tags,
        "failed_items": failed_items
    }


@app.route('/api/jobs/<job_id>/delete', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job (stops it first if running, does NOT cleanup Asana data)."""
    try:
        import time
        import os

        print(f"\n{'='*60}")
        print(f"Deleting job {job_id}")
        print(f"{'='*60}")

        # CRITICAL: Mark for deletion ATOMICALLY (this prevents background thread saves)
        print(f"Marking job {job_id} for deletion...")
        if not state_manager.mark_for_deletion(job_id):
            print(f"✗ Job not found")
            print(f"{'='*60}\n")
            return jsonify({
                "success": False,
                "error": "Job not found"
            }), 404
        print(f"✓ Deletion marker set")

        # Also mark job as stopped to prevent auto-restart
        print(f"Marking job {job_id} as stopped...")
        state_manager.update_job_status(job_id, "stopped")
        print(f"✓ Job status updated to 'stopped'")

        # Stop if running
        if job_id in running_services:
            print(f"Stopping service for job {job_id}...")
            service = running_services[job_id]

            # CRITICAL: Set all stop flags to force complete shutdown
            service.deleted = True  # Prevents state saves
            service.running = False  # Forces main loop to exit
            service.paused = True  # Additional safety
            print(f"✓ Set all stop flags (deleted=True, running=False, paused=True)")

            # Remove from tracking immediately to prevent any operations
            del running_services[job_id]
            thread = None
            if job_id in service_threads:
                thread = service_threads[job_id]
                del service_threads[job_id]
            print(f"✓ Removed from service tracking")

            # Wait for background thread to complete its current iteration
            # The thread checks self.running in the main loop, so it should exit
            print(f"Waiting for background thread to exit...")
            time.sleep(3)  # Increased from 0.5 to 3 seconds

            # Check if thread is still alive
            if thread and thread.is_alive():
                print(f"⚠ Thread still running after 3s, waiting additional 2s...")
                time.sleep(2)

            print(f"✓ Service thread should be stopped")

        # TOMBSTONE APPROACH: Keep the file with deletion marker instead of deleting immediately
        # This prevents Flask auto-reload from resurrecting the job
        # The file will be cleaned up later (manually or by a cleanup process)
        print(f"Job {job_id} marked for deletion (state file preserved with deletion marker)")
        print(f"✓ Job {job_id} deleted (file remains as tombstone to prevent resurrection)")
        print(f"{'='*60}\n")
        return jsonify({
            "success": True,
            "message": f"Job {job_id} deleted"
        })

    except Exception as e:
        import traceback
        print(f"✗ Error deleting job: {e}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/salesforce/cleanup', methods=['POST'])
def cleanup_salesforce_instance():
    """
    NUCLEAR OPTION: Clean up ALL Salesforce data in an instance.
    Deletes all accounts, opportunities, contacts, leads, cases, and campaigns.
    """
    try:
        data = request.json
        instance_url = data.get('tenant_id')
        user_tokens_data = data.get('user_tokens', [])

        if not instance_url or not user_tokens_data:
            return jsonify({
                "success": False,
                "error": "Missing instance_url or user_tokens"
            }), 400

        # Parse user credentials into format expected by SalesforceClientPool
        user_credentials = {}
        for user in user_tokens_data:
            user_credentials[user['name']] = {
                'username': user['username'],
                'password': user['password'],
                'security_token': user['security_token'],
                'instance_url': user.get('instance_url', instance_url)
            }

        # Create Salesforce client pool
        sf_pool = SalesforceClientPool(user_credentials)
        all_clients = sf_pool.get_valid_clients()

        if not all_clients:
            return jsonify({
                "success": False,
                "error": "No valid Salesforce credentials available for cleanup"
            }), 400

        print(f"\n{'='*60}")
        print(f"Starting INSTANCE-LEVEL cleanup for Salesforce instance {instance_url}")
        print(f"WARNING: This will delete ALL data objects!")
        print(f"{'='*60}\n")

        # Use the first valid client for cleanup
        client = all_clients[0]

        # Query and delete all objects using bulk operations
        deleted_accounts = 0
        deleted_opportunities = 0
        deleted_contacts = 0
        deleted_leads = 0
        deleted_cases = 0
        deleted_campaigns = 0
        failed_items = []

        def bulk_delete(object_type, records):
            """Delete records in batches of 200 (Salesforce limit)"""
            deleted = 0
            failed = []
            batch_size = 200

            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                batch_ids = [{'Id': record['Id']} for record in batch]

                try:
                    # Use bulk delete via simple-salesforce
                    results = client.sf.bulk.__getattr__(object_type).delete(batch_ids)

                    # Count successes and failures
                    for idx, result in enumerate(results):
                        if result['success']:
                            deleted += 1
                        else:
                            error_msg = result.get('errors', [{}])[0].get('message', 'Unknown error')
                            failed.append(f"{object_type} {batch[idx]['Id']}: {error_msg}")
                except Exception as e:
                    # If bulk fails, fall back to individual deletes for this batch
                    print(f"Bulk delete failed for {object_type}, falling back to individual deletes: {e}")
                    for record in batch:
                        try:
                            client.sf.__getattr__(object_type).delete(record['Id'])
                            deleted += 1
                        except Exception as del_e:
                            failed.append(f"{object_type} {record['Id']}: {str(del_e)}")

            return deleted, failed

        # Delete Campaigns
        try:
            campaigns = client.sf.query_all("SELECT Id FROM Campaign")['records']
            print(f"Found {len(campaigns)} campaigns to delete")
            if campaigns:
                deleted_campaigns, campaign_failures = bulk_delete('Campaign', campaigns)
                failed_items.extend(campaign_failures)
                print(f"Deleted {deleted_campaigns} campaigns")
        except Exception as e:
            print(f"Error querying campaigns: {e}")

        # Delete Cases
        try:
            cases = client.sf.query_all("SELECT Id FROM Case")['records']
            print(f"Found {len(cases)} cases to delete")
            if cases:
                deleted_cases, case_failures = bulk_delete('Case', cases)
                failed_items.extend(case_failures)
                print(f"Deleted {deleted_cases} cases")
        except Exception as e:
            print(f"Error querying cases: {e}")

        # Delete Opportunities
        try:
            opportunities = client.sf.query_all("SELECT Id FROM Opportunity")['records']
            print(f"Found {len(opportunities)} opportunities to delete")
            if opportunities:
                deleted_opportunities, opp_failures = bulk_delete('Opportunity', opportunities)
                failed_items.extend(opp_failures)
                print(f"Deleted {deleted_opportunities} opportunities")
        except Exception as e:
            print(f"Error querying opportunities: {e}")

        # Delete Contacts
        try:
            contacts = client.sf.query_all("SELECT Id FROM Contact")['records']
            print(f"Found {len(contacts)} contacts to delete")
            if contacts:
                deleted_contacts, contact_failures = bulk_delete('Contact', contacts)
                failed_items.extend(contact_failures)
                print(f"Deleted {deleted_contacts} contacts")
        except Exception as e:
            print(f"Error querying contacts: {e}")

        # Delete Leads
        try:
            leads = client.sf.query_all("SELECT Id FROM Lead")['records']
            print(f"Found {len(leads)} leads to delete")
            if leads:
                deleted_leads, lead_failures = bulk_delete('Lead', leads)
                failed_items.extend(lead_failures)
                print(f"Deleted {deleted_leads} leads")
        except Exception as e:
            print(f"Error querying leads: {e}")

        # Delete Accounts (must be last due to dependencies)
        try:
            accounts = client.sf.query_all("SELECT Id FROM Account")['records']
            print(f"Found {len(accounts)} accounts to delete")
            if accounts:
                deleted_accounts, account_failures = bulk_delete('Account', accounts)
                failed_items.extend(account_failures)
                print(f"Deleted {deleted_accounts} accounts")
        except Exception as e:
            print(f"Error querying accounts: {e}")

        print(f"\n{'='*60}")
        print(f"Salesforce instance cleanup complete!")
        print(f"Deleted: {deleted_accounts} accounts, {deleted_opportunities} opportunities, {deleted_contacts} contacts, {deleted_leads} leads, {deleted_cases} cases, {deleted_campaigns} campaigns")
        print(f"Failed: {len(failed_items)} items")
        print(f"{'='*60}\n")

        return jsonify({
            "success": True,
            "deleted_account": deleted_accounts,
            "deleted_opportunity": deleted_opportunities,
            "deleted_contact": deleted_contacts,
            "deleted_lead": deleted_leads,
            "deleted_case": deleted_cases,
            "deleted_campaign": deleted_campaigns,
            "failed_items": failed_items
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/okta/cleanup', methods=['POST'])
def cleanup_okta_org():
    """
    NUCLEAR OPTION: Clean up ALL Okta data in an organization.
    Deletes all users, groups, and app assignments.
    """
    try:
        data = request.json
        org_url = data.get('tenant_id')
        user_tokens_data = data.get('user_tokens', [])

        if not org_url or not user_tokens_data:
            return jsonify({
                "success": False,
                "error": "Missing org_url or user_tokens"
            }), 400

        # Parse user credentials
        user_credentials = {}
        for user in user_tokens_data:
            user_credentials[user['name']] = {
                'token': user['token'],
                'org_url': user.get('org_url', org_url)
            }

        # Create Okta client pool
        okta_pool = OktaClientPool(user_credentials)
        all_clients = okta_pool.get_valid_clients()

        if not all_clients:
            return jsonify({
                "success": False,
                "error": "No valid Okta API tokens available for cleanup"
            }), 400

        print(f"\n{'='*60}")
        print(f"Starting ORG-LEVEL cleanup for Okta org {org_url}")
        print(f"WARNING: This will delete ALL users, groups, and apps!")
        print(f"{'='*60}\n")

        # Use the first valid client for cleanup
        client = all_clients[0]

        deleted_users = 0
        deleted_groups = 0
        deleted_apps = 0
        failed_items = []

        # Delete all users
        try:
            users = client.okta.list_users()
            print(f"Found {len(users)} users")
            for user in users:
                try:
                    client.okta.deactivate_user(user['id'])
                    client.okta.delete_user(user['id'])
                    deleted_users += 1
                except Exception as e:
                    failed_items.append(f"User {user['id']}: {str(e)}")
        except Exception as e:
            print(f"Error querying users: {e}")

        # Delete all groups
        try:
            groups = client.okta.list_groups()
            print(f"Found {len(groups)} groups")
            for group in groups:
                try:
                    client.okta.delete_group(group['id'])
                    deleted_groups += 1
                except Exception as e:
                    failed_items.append(f"Group {group['id']}: {str(e)}")
        except Exception as e:
            print(f"Error querying groups: {e}")

        # Delete all applications
        try:
            apps = client.okta.list_applications()
            print(f"Found {len(apps)} applications")
            for app in apps:
                try:
                    client.okta.deactivate_application(app['id'])
                    client.okta.delete_application(app['id'])
                    deleted_apps += 1
                except Exception as e:
                    failed_items.append(f"App {app['id']}: {str(e)}")
        except Exception as e:
            print(f"Error querying apps: {e}")

        print(f"\n{'='*60}")
        print(f"Okta org cleanup complete!")
        print(f"Deleted: {deleted_users} users, {deleted_groups} groups, {deleted_apps} apps")
        print(f"Failed: {len(failed_items)} items")
        print(f"{'='*60}\n")

        return jsonify({
            "success": True,
            "deleted_user": deleted_users,
            "deleted_group": deleted_groups,
            "deleted_app": deleted_apps,
            "failed_items": failed_items
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/validate_token', methods=['POST'])
def validate_token():
    """Validate an API token (supports Asana and Okta)."""
    try:
        data = request.json
        connection_type = data.get('connection_type', 'asana')

        if connection_type == 'asana':
            api_key = data.get('api_key')

            if not api_key:
                return jsonify({
                    "success": False,
                    "error": "No API key provided"
                }), 400

            from continuous.asana_client import AsanaClient
            client = AsanaClient(api_key)

            if client.validate_token():
                user_info = client.get_user_info()
                return jsonify({
                    "success": True,
                    "valid": True,
                    "connection_type": "asana",
                    "user": {
                        "name": user_info.get("name"),
                        "email": user_info.get("email")
                    }
                })
            else:
                return jsonify({
                    "success": True,
                    "valid": False,
                    "connection_type": "asana"
                })

        elif connection_type == 'okta':
            token = data.get('token') or data.get('api_key')
            org_url = data.get('org_url')

            if not token:
                return jsonify({
                    "success": False,
                    "error": "No token provided"
                }), 400

            if not org_url:
                return jsonify({
                    "success": False,
                    "error": "No org_url provided"
                }), 400

            from continuous.connections.okta_connection import OktaConnection

            try:
                client = OktaConnection(token, org_url, "validator")

                if client.validate_token():
                    user_info = client.get_user_info()
                    profile = user_info.get("profile", {})
                    return jsonify({
                        "success": True,
                        "valid": True,
                        "connection_type": "okta",
                        "user": {
                            "name": f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip(),
                            "email": profile.get("email"),
                            "id": user_info.get("id")
                        }
                    })
                else:
                    return jsonify({
                        "success": True,
                        "valid": False,
                        "connection_type": "okta"
                    })
            except Exception as e:
                return jsonify({
                    "success": False,
                    "valid": False,
                    "connection_type": "okta",
                    "error": str(e)
                }), 401

        elif connection_type == 'salesforce':
            username = data.get('username')
            password = data.get('password')
            security_token = data.get('security_token')
            instance_url = data.get('instance_url')

            if not username:
                return jsonify({
                    "success": False,
                    "error": "No username provided"
                }), 400

            if not password:
                return jsonify({
                    "success": False,
                    "error": "No password provided"
                }), 400

            if not security_token:
                return jsonify({
                    "success": False,
                    "error": "No security_token provided"
                }), 400

            if not instance_url:
                return jsonify({
                    "success": False,
                    "error": "No instance_url provided"
                }), 400

            from continuous.connections.salesforce_connection import SalesforceConnection

            try:
                client = SalesforceConnection(
                    api_key="",  # Not used for Salesforce
                    user_name="validator",
                    username=username,
                    password=password,
                    security_token=security_token,
                    instance_url=instance_url
                )

                if client.validate_token():
                    user_info = client.get_user_info()
                    return jsonify({
                        "success": True,
                        "valid": True,
                        "connection_type": "salesforce",
                        "user": {
                            "name": user_info.get("Name"),
                            "email": user_info.get("Email"),
                            "id": user_info.get("Id")
                        }
                    })
                else:
                    return jsonify({
                        "success": True,
                        "valid": False,
                        "connection_type": "salesforce"
                    })
            except Exception as e:
                return jsonify({
                    "success": False,
                    "valid": False,
                    "connection_type": "salesforce",
                    "error": str(e)
                }), 401

        else:
            return jsonify({
                "success": False,
                "error": f"Unsupported connection type: {connection_type}"
            }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/workspaces', methods=['POST'])
def get_workspaces():
    """Get workspaces for an Asana API key."""
    try:
        data = request.json
        api_key = data.get('api_key')

        if not api_key:
            return jsonify({
                "success": False,
                "error": "No API key provided"
            }), 400

        import requests
        response = requests.get(
            "https://app.asana.com/api/1.0/workspaces",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        response.raise_for_status()

        workspaces = response.json()["data"]

        return jsonify({
            "success": True,
            "workspaces": workspaces
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/okta/orgs', methods=['POST'])
def get_okta_orgs():
    """Get Okta org information and validate access."""
    try:
        data = request.json
        token = data.get('token') or data.get('api_key')
        org_url = data.get('org_url')

        if not token:
            return jsonify({
                "success": False,
                "error": "No token provided"
            }), 400

        if not org_url:
            return jsonify({
                "success": False,
                "error": "No org_url provided"
            }), 400

        from continuous.connections.okta_connection import OktaConnection

        client = OktaConnection(token, org_url, "temp")

        # Validate token first
        if not client.validate_token():
            return jsonify({
                "success": False,
                "error": "Invalid Okta token or org_url"
            }), 401

        # Get org information
        user_info = client.get_user_info()

        # Get counts for users, groups, and apps
        users = client.list_users(limit=1)
        groups = client.list_groups(limit=1)
        apps = client.list_apps(limit=1)

        # Extract org name from URL
        org_name = org_url.replace("https://", "").replace(".okta.com", "").replace(".oktapreview.com", "")

        return jsonify({
            "success": True,
            "org": {
                "org_url": org_url,
                "org_name": org_name,
                "accessible": True,
                "authenticated_user": {
                    "name": f"{user_info.get('profile', {}).get('firstName', '')} {user_info.get('profile', {}).get('lastName', '')}".strip(),
                    "email": user_info.get('profile', {}).get('email')
                }
            }
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/okta/apps', methods=['POST'])
def get_okta_apps():
    """List applications in Okta org."""
    try:
        data = request.json
        token = data.get('token') or data.get('api_key')
        org_url = data.get('org_url')
        limit = data.get('limit', 50)

        if not token:
            return jsonify({
                "success": False,
                "error": "No token provided"
            }), 400

        if not org_url:
            return jsonify({
                "success": False,
                "error": "No org_url provided"
            }), 400

        from continuous.connections.okta_connection import OktaConnection

        client = OktaConnection(token, org_url, "temp")

        # Validate token first
        if not client.validate_token():
            return jsonify({
                "success": False,
                "error": "Invalid Okta token or org_url"
            }), 401

        # List apps
        apps = client.list_apps(limit=limit)

        # Format app data for frontend
        formatted_apps = []
        for app in apps:
            formatted_apps.append({
                "id": app.get("id"),
                "name": app.get("label") or app.get("name"),
                "label": app.get("label"),
                "status": app.get("status"),
                "created": app.get("created"),
                "lastUpdated": app.get("lastUpdated")
            })

        return jsonify({
            "success": True,
            "apps": formatted_apps,
            "total": len(formatted_apps)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/okta/users', methods=['POST'])
def get_okta_users():
    """List users in Okta org."""
    try:
        data = request.json
        token = data.get('token') or data.get('api_key')
        org_url = data.get('org_url')
        limit = data.get('limit', 50)

        if not token:
            return jsonify({
                "success": False,
                "error": "No token provided"
            }), 400

        if not org_url:
            return jsonify({
                "success": False,
                "error": "No org_url provided"
            }), 400

        from continuous.connections.okta_connection import OktaConnection

        client = OktaConnection(token, org_url, "temp")

        # Validate token first
        if not client.validate_token():
            return jsonify({
                "success": False,
                "error": "Invalid Okta token or org_url"
            }), 401

        # List users
        users = client.list_users(limit=limit)

        # Format user data for frontend
        formatted_users = []
        for user in users:
            profile = user.get("profile", {})
            formatted_users.append({
                "id": user.get("id"),
                "name": f"{profile.get('firstName', '')} {profile.get('lastName', '')}".strip(),
                "email": profile.get("email"),
                "login": profile.get("login"),
                "status": user.get("status"),
                "created": user.get("created"),
                "lastUpdated": user.get("lastUpdated")
            })

        return jsonify({
            "success": True,
            "users": formatted_users,
            "total": len(formatted_users)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/okta/groups', methods=['POST'])
def get_okta_groups():
    """List groups in Okta org."""
    try:
        data = request.json
        token = data.get('token') or data.get('api_key')
        org_url = data.get('org_url')
        limit = data.get('limit', 50)

        if not token:
            return jsonify({
                "success": False,
                "error": "No token provided"
            }), 400

        if not org_url:
            return jsonify({
                "success": False,
                "error": "No org_url provided"
            }), 400

        from continuous.connections.okta_connection import OktaConnection

        client = OktaConnection(token, org_url, "temp")

        # Validate token first
        if not client.validate_token():
            return jsonify({
                "success": False,
                "error": "Invalid Okta token or org_url"
            }), 401

        # List groups
        groups = client.list_groups(limit=limit)

        # Format group data for frontend
        formatted_groups = []
        for group in groups:
            profile = group.get("profile", {})
            formatted_groups.append({
                "id": group.get("id"),
                "name": profile.get("name"),
                "description": profile.get("description"),
                "type": group.get("type"),
                "created": group.get("created"),
                "lastUpdated": group.get("lastUpdated")
            })

        return jsonify({
            "success": True,
            "groups": formatted_groups,
            "total": len(formatted_groups)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "success": True,
        "status": "running",
        "active_jobs": len(running_services),
        "connection_types_supported": ["asana", "okta", "salesforce"],
        "version": "2.0.0"
    })


if __name__ == '__main__':
    print("=" * 60)
    print("Multi-Platform Continuous Data Generator - API Server")
    print("Supported Platforms: Asana, Okta, Salesforce")
    print("=" * 60)
    print()
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting server on http://localhost:{port}")
    print(f"Open http://localhost:{port} in your browser")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)

    # Restart any jobs that were running
    restart_running_jobs()

    # Start Flask server
    app.run(debug=True, host='0.0.0.0', port=port, threaded=True)
