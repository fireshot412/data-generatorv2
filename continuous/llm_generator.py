#!/usr/bin/env python3
"""
LLM Generator for creating realistic Asana content using Claude API.
Generates industry-specific project names, task names, comments, and more.
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import anthropic
import json
import random
import re


class LLMGenerator:
    """Generates realistic workplace content using Claude API."""

    # Industry-specific context for better content generation
    INDUSTRIES = {
        "finance": "Finance/Banking industry with focus on compliance, audits, and financial reporting",
        "healthcare": "Healthcare/Life Sciences with HIPAA compliance, patient care, and medical research",
        "manufacturing": "Manufacturing/Industrial with production lines, quality control, and supply chain",
        "travel": "Travel/Hospitality with bookings, customer service, and seasonal operations",
        "technology": "Technology/Software with product development, engineering sprints, and deployments",
        "retail": "Retail/E-commerce with inventory, sales, marketing campaigns, and customer experience",
        "education": "Education sector with curriculum, student services, and academic programs",
        "government": "Government/Public Sector with regulations, public services, and policy implementation",
        "energy": "Energy/Utilities with infrastructure, compliance, and operational maintenance",
        "media": "Media/Entertainment with content creation, production schedules, and distribution"
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM generator with Claude API.

        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY must be provided or set as environment variable")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-haiku-20240307"  # Claude Haiku 3 - cost effective and reliable

        # Track API usage for cost awareness
        self.api_calls_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def _get_time_context(self, current_time: Optional[datetime] = None) -> str:
        """
        Generate time-aware context string for more realistic content.

        Args:
            current_time: Current time (defaults to now)

        Returns:
            Context string about the time of day/week
        """
        if current_time is None:
            current_time = datetime.now()

        hour = current_time.hour
        day_of_week = current_time.weekday()  # 0=Monday, 6=Sunday

        # Weekend check
        if day_of_week >= 5:  # Saturday or Sunday
            return " (Note: It's the weekend, so this activity happening now would be unusual - maybe urgent or someone catching up)"

        # Time of day contexts
        if hour < 6:
            return " (Note: It's very early morning/late night - this would be unusual, perhaps urgent or someone working odd hours)"
        elif hour < 9:
            return " (Note: It's early morning before typical work hours - perhaps someone starting early)"
        elif 9 <= hour < 12:
            return ""  # Normal morning work hours
        elif 12 <= hour < 13:
            return " (Note: It's around lunch time)"
        elif 13 <= hour < 18:
            return ""  # Normal afternoon work hours
        elif 18 <= hour < 21:
            return " (Note: It's after typical work hours - perhaps someone working late or in a different timezone)"
        else:  # 21:00 - 05:59
            return " (Note: It's late at night - this activity would be unusual, maybe urgent, someone in a different timezone, or catching up on work)"

    def _call_claude(self, prompt: str, max_tokens: int = 200) -> str:
        """
        Make API call to Claude and track usage.

        Args:
            prompt: The prompt to send to Claude
            max_tokens: Maximum tokens in response

        Returns:
            Generated text from Claude
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            # Track usage
            self.api_calls_count += 1
            self.total_input_tokens += message.usage.input_tokens
            self.total_output_tokens += message.usage.output_tokens

            return message.content[0].text.strip()

        except Exception as e:
            import traceback
            print(f"\n{'='*60}")
            print(f"ERROR calling Claude API: {e}")
            print(f"Error type: {type(e).__name__}")
            print(f"Traceback:")
            traceback.print_exc()
            print(f"{'='*60}\n")
            # Fallback to generic content if API fails
            return self._generate_fallback_content(prompt)

    def _generate_fallback_content(self, prompt: str) -> str:
        """Generate basic fallback content if API fails."""
        if "project name" in prompt.lower():
            return "New Project"
        elif "task name" in prompt.lower():
            return "New Task"
        elif "comment" in prompt.lower():
            return "Working on this."
        elif "group name" in prompt.lower():
            # Generate a more appropriate group name fallback
            if "team" in prompt.lower():
                return "Engineering - Core Team"
            elif "role" in prompt.lower():
                return "Engineering Managers"
            elif "project" in prompt.lower():
                return "Project Alpha"
            elif "location" in prompt.lower():
                return "San Francisco Office"
            else:
                return "Engineering Department"
        elif "group description" in prompt.lower() or "description for" in prompt.lower():
            return "Team responsible for core operations and strategic initiatives"
        elif "profile update" in prompt.lower() or "user profile update" in prompt.lower():
            return "Profile updated as part of organizational changes"
        elif "activity" in prompt.lower():
            return "User activity recorded in system"
        return "Content generated"

    def generate_project_name(self, industry: str, context: Optional[str] = None) -> str:
        """
        Generate realistic project name for given industry.

        Args:
            industry: Industry type (e.g., 'finance', 'healthcare')
            context: Optional additional context about the project

        Returns:
            Generated project name
        """
        industry_context = self.INDUSTRIES.get(industry.lower(), "General business")

        prompt = f"""You are generating a realistic project name for a {industry_context} team.

Context: {context if context else "A typical project for this industry"}

Generate a realistic, professional project name that would be used in {industry_context}.
The name should be 3-8 words, specific to the industry, and sound like real workplace project.

Examples for different industries:
- Finance: "Q4 2024 Compliance Audit"
- Healthcare: "Electronic Health Records Migration"
- Manufacturing: "Assembly Line Automation Phase 2"

Return ONLY the project name, nothing else."""

        return self._call_claude(prompt, max_tokens=50)

    def generate_project_description(self, industry: str, project_name: str) -> str:
        """
        Generate realistic project description.

        Args:
            industry: Industry type
            project_name: Name of the project

        Returns:
            Generated project description
        """
        industry_context = self.INDUSTRIES.get(industry.lower(), "General business")

        prompt = f"""You are generating a realistic project description for a {industry_context} team.

Project: {project_name}
Industry: {industry_context}

Generate a brief but informative project description (2-4 sentences) that explains the project's goals and context.
Make it contextually relevant to {industry_context}.

Return ONLY the description, nothing else."""

        return self._call_claude(prompt, max_tokens=200)

    def generate_task_name(self, industry: str, project_name: str,
                          task_type: Optional[str] = None) -> str:
        """
        Generate realistic task name for a project.

        Args:
            industry: Industry type
            project_name: Name of the parent project
            task_type: Optional type of task (e.g., 'design', 'implementation', 'review')

        Returns:
            Generated task name
        """
        industry_context = self.INDUSTRIES.get(industry.lower(), "General business")
        type_hint = f" (specifically a {task_type} task)" if task_type else ""

        prompt = f"""You are generating a realistic task name for a {industry_context} team.

Project: {project_name}
Industry: {industry_context}
{f"Task Type: {task_type}" if task_type else ""}

Generate a specific, actionable task name that would be part of this project{type_hint}.
The task should be 3-10 words and sound like real work.

Return ONLY the task name, nothing else."""

        return self._call_claude(prompt, max_tokens=50)

    def generate_task_description(self, industry: str, project_name: str,
                                  task_name: str) -> str:
        """
        Generate realistic task description.

        Args:
            industry: Industry type
            project_name: Name of the parent project
            task_name: Name of the task

        Returns:
            Generated task description
        """
        industry_context = self.INDUSTRIES.get(industry.lower(), "General business")

        prompt = f"""You are generating a realistic task description for a {industry_context} team.

Project: {project_name}
Task: {task_name}

Generate a brief but specific task description (1-3 sentences) that explains what needs to be done.
Make it contextually relevant to {industry_context}.

Return ONLY the description, nothing else."""

        return self._call_claude(prompt, max_tokens=150)

    def generate_comment_starting_work(self, user_name: str, task_name: str,
                                      current_time: Optional[datetime] = None) -> str:
        """
        Generate comment for when user starts working on a task.

        Args:
            user_name: Name of the user starting work
            task_name: Name of the task
            current_time: Current time for context-aware generation

        Returns:
            Generated comment
        """
        time_context = self._get_time_context(current_time)

        prompt = f"""Generate a brief, natural comment from {user_name} saying they're starting work on: "{task_name}"{time_context}

The comment should be 1-2 sentences, casual but professional, like real workplace communication.
If the time context suggests unusual hours, incorporate that naturally into the comment.

Examples for normal hours:
- "Picking this up now, should have it done by EOD"
- "Starting work on this. Will update with progress later today."
- "Got it! Beginning implementation."

Examples for off-hours:
- "Sorry for the late night post but picking this up now - needed urgently for tomorrow"
- "Jumping on this early before meetings start"
- "Quick weekend check-in - starting on this urgent item"

Return ONLY the comment, nothing else."""

        return self._call_claude(prompt, max_tokens=120)

    def generate_comment_progress_update(self, user_name: str, task_name: str,
                                        industry: str, current_time: Optional[datetime] = None) -> str:
        """
        Generate progress update comment.

        Args:
            user_name: Name of the user
            task_name: Name of the task
            industry: Industry type for context
            current_time: Current time for context-aware generation

        Returns:
            Generated comment
        """
        industry_context = self.INDUSTRIES.get(industry.lower(), "General business")
        time_context = self._get_time_context(current_time)

        prompt = f"""Generate a brief progress update comment from {user_name} about: "{task_name}"
Context: {industry_context}{time_context}

The comment should mention specific progress, be 1-2 sentences, and feel natural.
If the time context suggests unusual hours, acknowledge it naturally.

Examples for normal hours:
- "About 60% done - the data migration is taking longer than expected"
- "Making good progress. Just finished the first draft, moving to review phase."
- "Hit a minor snag with the API integration but working through it"

Examples for off-hours:
- "Quick late-night update: about 75% done, should finish tomorrow"
- "Early morning progress check - almost ready for the 9am review"

Return ONLY the comment, nothing else."""

        return self._call_claude(prompt, max_tokens=120)

    def generate_comment_blocked(self, user_name: str, task_name: str,
                                 industry: str) -> str:
        """
        Generate realistic blocker comment.

        Args:
            user_name: Name of the user
            task_name: Name of the task
            industry: Industry type for context

        Returns:
            Generated comment explaining blocker
        """
        industry_context = self.INDUSTRIES.get(industry.lower(), "General business")

        prompt = f"""Generate a realistic blocker comment from {user_name} about: "{task_name}"
Context: {industry_context}

The comment should explain what's blocking progress, be 1-3 sentences, and mention who/what they're waiting on.

Examples:
- "Blocked - waiting on security review from InfoSec team before proceeding"
- "Can't move forward until we get approval from compliance. @Sarah can you help expedite?"
- "Stuck waiting on the design mockups from the UX team"

Return ONLY the comment, nothing else."""

        return self._call_claude(prompt, max_tokens=120)

    def generate_comment_unblocked(self, user_name: str, blocker_reason: Optional[str] = None) -> str:
        """
        Generate comment for when task is unblocked.

        Args:
            user_name: Name of the user
            blocker_reason: Optional reason for original block

        Returns:
            Generated comment
        """
        context = f" The blocker was: {blocker_reason}" if blocker_reason else ""

        prompt = f"""Generate a brief comment from {user_name} saying the blocker is resolved and they're moving forward.{context}

The comment should be 1-2 sentences, positive, and indicate they're resuming work.

Examples:
- "Got the approval! Moving forward now."
- "Blocker resolved - back on this."
- "Security review completed. Resuming implementation."

Return ONLY the comment, nothing else."""

        return self._call_claude(prompt, max_tokens=80)

    def generate_comment_completed(self, user_name: str, task_name: str,
                                   industry: str, current_time: Optional[datetime] = None) -> str:
        """
        Generate completion comment.

        Args:
            user_name: Name of the user
            task_name: Name of the task
            industry: Industry type for context
            current_time: Current time for context-aware generation

        Returns:
            Generated completion comment
        """
        industry_context = self.INDUSTRIES.get(industry.lower(), "General business")
        time_context = self._get_time_context(current_time)

        prompt = f"""Generate a brief completion comment from {user_name} for: "{task_name}"
Context: {industry_context}{time_context}

The comment should indicate the task is done, be 1-2 sentences, and sound satisfied/accomplished.
If the time context suggests unusual hours, acknowledge it naturally.

Examples for normal hours:
- "Done! Deployed to production and monitoring for issues."
- "Completed. Documentation updated and ready for review."
- "Finished ahead of schedule. All tests passing."

Examples for off-hours:
- "Finally done! Late night push but it's deployed and working"
- "Got it done early - ready for the morning review"

Return ONLY the comment, nothing else."""

        return self._call_claude(prompt, max_tokens=120)

    def generate_comment_reassignment(self, old_user: str, new_user: str,
                                     task_name: str, reason: Optional[str] = None) -> str:
        """
        Generate comment for task reassignment.

        Args:
            old_user: Previous assignee
            new_user: New assignee
            task_name: Name of the task
            reason: Optional reason for reassignment

        Returns:
            Generated comment
        """
        reason_context = f" Reason: {reason}" if reason else ""

        prompt = f"""Generate a brief comment about reassigning "{task_name}" from {old_user} to {new_user}.{reason_context}

The comment should be 1-2 sentences and professional.

Examples:
- "@{new_user} Can you take this over? I'm swamped with the other project."
- "Reassigning to @{new_user} who has more context on this area"
- "@{new_user} - moving this to you since you're handling the related tasks"

Return ONLY the comment, nothing else."""

        return self._call_claude(prompt, max_tokens=100)

    def generate_comment_conversation(self, user_name: str, responding_to: str,
                                     previous_comment: str, task_name: str) -> str:
        """
        Generate conversational comment in response to another comment.

        Args:
            user_name: Name of the user making the comment
            responding_to: Name of user being responded to
            previous_comment: The comment being responded to
            task_name: Name of the task

        Returns:
            Generated response comment
        """
        prompt = f"""Generate a brief conversational reply from {user_name} to {responding_to} about: "{task_name}"

Previous comment from {responding_to}: "{previous_comment}"

Generate a natural, helpful response that moves the conversation forward. 1-2 sentences.

Examples:
- "Good question - let me check with the team and get back to you"
- "Yes, that approach should work. Go ahead and implement it."
- "I can help with that. Let me review and I'll provide feedback by EOD"

Return ONLY the comment, nothing else."""

        return self._call_claude(prompt, max_tokens=100)

    def generate_contextual_initial_comment(self, user_name: str, task_name: str,
                                           project_name: str, industry: str,
                                           existing_comments: List[Dict[str, str]]) -> str:
        """
        Generate contextual initial comment based on existing comments in conversation thread.
        MATURE APPROACH: Queries task context and generates realistic conversational responses.

        Args:
            user_name: Name of the user making the comment
            task_name: Name of the task
            project_name: Name of the project
            industry: Industry type for context
            existing_comments: List of existing comments with 'user' and 'comment' keys

        Returns:
            Generated contextual comment
        """
        industry_context = self.INDUSTRIES.get(industry.lower(), "General business")

        if not existing_comments:
            # First comment - 50% chance to be a question/request (to start conversations)
            # This ensures conversations begin with questions that need responses
            import random
            is_question = random.random() < 0.5

            if is_question:
                prompt = f"""Generate a brief, natural comment from {user_name} about task: "{task_name}" in project: "{project_name}"
Context: {industry_context}

The comment should be a QUESTION or REQUEST for information/update. 1-2 sentences, casual but professional.

Examples:
- "Can someone give me more context on this task?"
- "What's the current status on this?"
- "Do we have any blockers here?"
- "Anyone started looking at this yet?"
- "Need any help with this one?"
- "What's the priority level for this?"
- "Should I coordinate with anyone before starting?"

Return ONLY the comment, nothing else."""
            else:
                prompt = f"""Generate a brief, natural initial comment from {user_name} about starting work on task: "{task_name}" in project: "{project_name}"
Context: {industry_context}

The comment should be 1-2 sentences, casual but professional.

Examples:
- "Starting work on this task."
- "I'll tackle this one today."
- "Looking into this now."
- "Great, I'll get this done by EOD."
- "On it!"

Return ONLY the comment, nothing else."""

            return self._call_claude(prompt, max_tokens=80)

        else:
            # Follow-up comment - generate conversational response based on context
            last_comment = existing_comments[-1]
            last_commenter = last_comment.get("user", "Unknown")
            last_comment_text = last_comment.get("comment", "")

            # Build FULL conversation history string (not just last 3)
            # This gives LLM complete context to avoid any repetition
            conversation_history = "\n".join([
                f"- {c.get('user', 'Unknown')}: \"{c.get('comment', '')}\""
                for c in existing_comments  # ALL comments for full context
            ])

            # Extract all opening phrases from existing comments to avoid repetition
            used_phrases = []
            for comment in existing_comments:
                comment_text = comment.get("comment", "")
                # Extract first 5 words as the "opening phrase"
                words = comment_text.split()[:5]
                if words:
                    used_phrases.append(" ".join(words))

            # Detect if last comment was a question (contains '?')
            last_was_question = '?' in last_comment_text

            # Detect if this user was mentioned/directed to
            user_was_mentioned = user_name.lower() in last_comment_text.lower()

            if last_was_question:
                # If last comment was a question, generate a helpful ANSWER
                # Add context if the question was specifically directed at this user
                directed_note = ""
                if user_was_mentioned:
                    directed_note = f"\n\nNOTE: {last_commenter} specifically asked YOU ({user_name}) this question. Your response should acknowledge this."

                prompt = f"""Generate a natural ANSWER from {user_name} responding to {last_commenter}'s question on task: "{task_name}"
Context: {industry_context}
Project: {project_name}

Recent conversation history:
{conversation_history}

{last_commenter} asked: "{last_comment_text}"{directed_note}

Generate a helpful, specific answer that:
- Directly addresses the question
- Provides useful information or context
- Is 1-2 sentences, casual but professional
- Moves the conversation forward

Examples of good answers:
- "It's medium priority - should be done by Friday."
- "No blockers yet, I'm about halfway through."
- "Yeah, let's sync with the design team first."
- "I haven't started yet, planning to tackle it tomorrow."
- "No help needed for now, thanks! I'll reach out if I hit any issues."

Return ONLY the comment, nothing else."""
            else:
                # Otherwise, generate a follow-up (which might be a question or acknowledgement)
                # Build list of used phrases to explicitly avoid
                phrases_list = "\n".join([f"  - \"{phrase}...\"" for phrase in used_phrases]) if used_phrases else "  (none yet)"

                prompt = f"""Generate a natural follow-up comment from {user_name} on task: "{task_name}"
Context: {industry_context}
Project: {project_name}

Recent conversation history:
{conversation_history}

Last comment was from {last_commenter}: "{last_comment_text}"

ALREADY USED opening phrases that you MUST NOT repeat:
{phrases_list}

CRITICAL RULES:
1. DO NOT use any of the phrases listed above or anything similar
2. DO NOT repeat concepts already stated (like "let's dive into", "get started", "looking forward")
3. If someone already asked for an update, don't ask again - respond differently
4. Generate a contextual response that:
   - Uses a COMPLETELY UNIQUE opening phrase
   - Moves the conversation forward naturally
   - Is 1-2 sentences maximum
   - Sounds like real workplace communication

VARY your approach - try different structures:
- Specific question: "What's blocking this?", "Need design review first?", "ETA on requirements?"
- Status update: "Halfway through the analysis", "Found 3 integration points", "Scheduled for tomorrow"
- Coordination: "I'll sync with the team", "Let's review together Friday", "Can you handle X while I do Y?"
- Direct action: "Starting now", "Reviewing the specs", "Testing the integration"
- Simple acknowledgment: "On it", "Will do", "Noted"

Return ONLY the comment, nothing else."""

            return self._call_claude(prompt, max_tokens=120)

    def generate_comment_out_of_office(self, user_name: str, reason: str = "generic") -> str:
        """
        Generate realistic out-of-office or unavailability comment.

        Args:
            user_name: Name of the user
            reason: Reason type ('sick', 'pto', 'busy', 'generic')

        Returns:
            Generated OOO comment
        """
        reason_context = {
            "sick": "They have a sick child or are not feeling well",
            "pto": "They're taking planned time off",
            "busy": "They're heads down on another priority",
            "generic": "They're unavailable for some reason"
        }

        context = reason_context.get(reason, reason_context["generic"])

        prompt = f"""Generate a brief, realistic out-of-office or unavailability comment from {user_name}.
Context: {context}

The comment should be 1-2 sentences and sound natural.

Examples:
- "Signing off early today - sick kiddo needs pickup from school"
- "Out tomorrow for PTO. Back on Monday."
- "Heads down on the Q4 project this week. Will be less responsive."

Return ONLY the comment, nothing else."""

        return self._call_claude(prompt, max_tokens=80)

    def generate_subtask_names(self, industry: str, parent_task_name: str,
                              num_subtasks: int = 3) -> List[str]:
        """
        Generate multiple related subtask names for a parent task.

        Args:
            industry: Industry type
            parent_task_name: Name of the parent task
            num_subtasks: Number of subtasks to generate

        Returns:
            List of generated subtask names
        """
        industry_context = self.INDUSTRIES.get(industry.lower(), "General business")

        prompt = f"""Generate {num_subtasks} realistic subtask names for a {industry_context} team.

Parent Task: {parent_task_name}

Generate {num_subtasks} specific, actionable subtasks that would logically break down this parent task.
Each subtask should be 3-8 words.

Return the subtasks as a numbered list:
1. First subtask
2. Second subtask
3. Third subtask"""

        response = self._call_claude(prompt, max_tokens=200)

        # Parse the numbered list
        subtasks = []
        for line in response.split('\n'):
            line = line.strip()
            # Remove numbering (e.g., "1.", "1)", "1 -", etc.)
            if line and any(line[0:2].startswith(str(i)) for i in range(1, 10)):
                # Find the first letter after the number
                task_start = 2
                while task_start < len(line) and not line[task_start].isalpha():
                    task_start += 1
                if task_start < len(line):
                    subtasks.append(line[task_start:].strip())

        # Fallback if parsing failed
        if len(subtasks) < num_subtasks:
            subtasks = [f"Subtask {i+1} for {parent_task_name}" for i in range(num_subtasks)]

        return subtasks[:num_subtasks]

    def get_usage_stats(self) -> Dict[str, int]:
        """
        Get API usage statistics.

        Returns:
            Dictionary with usage stats
        """
        return {
            "api_calls": self.api_calls_count,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens
        }

    def reset_usage_stats(self):
        """Reset usage statistics counters."""
        self.api_calls_count = 0
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    # ============================================================================
    # OKTA-SPECIFIC CONTENT GENERATION METHODS
    # ============================================================================

    def generate_user_profile(
        self,
        industry: str,
        department: str,
        title: str,
        org_size: str = "midsize"
    ) -> Dict[str, Any]:
        """
        Generate realistic Okta user profile with diverse, culturally appropriate names.

        Args:
            industry: Industry type (e.g., 'healthcare', 'technology', 'finance')
            department: Department name (e.g., 'Engineering', 'Sales', 'Clinical')
            title: Job title (e.g., 'Software Engineer', 'Sales Manager')
            org_size: Organization size ('startup', 'midsize', 'enterprise')

        Returns:
            Dictionary with user profile data in JSON format

        Example:
            >>> profile = generator.generate_user_profile(
            ...     industry='technology',
            ...     department='Engineering',
            ...     title='Senior Software Engineer',
            ...     org_size='midsize'
            ... )
            >>> print(profile['firstName'])
            'Priya'
        """
        industry_context = self.INDUSTRIES.get(industry.lower(), "General business")

        # Build context for org size
        org_size_context = {
            "startup": "small startup (10-50 employees, flat structure)",
            "midsize": "mid-size company (100-500 employees, established departments)",
            "enterprise": "large enterprise (1000+ employees, complex hierarchy)"
        }.get(org_size, "mid-size company")

        prompt = f"""Generate a realistic user profile for an employee at a {org_size_context} in the {industry_context}.

Department: {department}
Job Title: {title}
Organization Size: {org_size}

Create a diverse, culturally appropriate profile with:
1. First and last name (be culturally diverse - use names from various ethnicities and backgrounds)
2. Professional email address
3. Mobile phone number (US format)
4. Employee details appropriate for the org size

Return ONLY valid JSON with this structure:
{{
    "firstName": "string",
    "lastName": "string",
    "email": "string",
    "login": "string",
    "mobilePhone": "string",
    "employeeNumber": "string",
    "manager": "string (manager's full name)",
    "location": "string (city, state)",
    "startDate": "YYYY-MM-DD",
    "division": "string",
    "costCenter": "string"
}}

Important:
- Generate realistic, diverse names from various cultures (Asian, European, African, Latino, etc.)
- Email should use company domain (e.g., @company.com, @techcorp.io)
- Phone numbers should be realistic US format (+1-XXX-XXX-XXXX)
- Start date should be between 6 months and 5 years ago
- Manager name should also be culturally diverse
- Location should be a real US city appropriate for the industry"""

        try:
            response = self._call_claude(prompt, max_tokens=400)

            # Extract JSON from response
            json_match = re.search(r'\{[^{}]*\{?[^{}]*\}?[^{}]*\}', response, re.DOTALL)
            if json_match:
                profile_data = json.loads(json_match.group())

                # Validate and clean the data
                required_fields = ["firstName", "lastName", "email", "login"]
                if all(field in profile_data for field in required_fields):
                    # Ensure login matches email if not specified differently
                    if not profile_data.get("login"):
                        profile_data["login"] = profile_data["email"]

                    # Add department and title to profile
                    profile_data["department"] = department
                    profile_data["title"] = title

                    return profile_data

        except (json.JSONDecodeError, Exception) as e:
            print(f"Error generating user profile via LLM: {e}")

        # Fallback to template-based generation
        return self._generate_fallback_user_profile(industry, department, title, org_size)

    def _generate_fallback_user_profile(
        self,
        industry: str,
        department: str,
        title: str,
        org_size: str
    ) -> Dict[str, Any]:
        """Generate fallback user profile using templates."""
        # Diverse name pools
        first_names = [
            "Priya", "Chen", "Maria", "Ahmed", "Yuki", "Oluwaseun", "Emma", "Carlos",
            "Fatima", "Raj", "Sofia", "Ibrahim", "Mei", "Diego", "Aisha", "Viktor",
            "Lucia", "Mohammed", "Yuna", "Gabriel", "Amara", "Hiroshi", "Isabella"
        ]
        last_names = [
            "Sharma", "Wang", "Rodriguez", "Hassan", "Tanaka", "Adeyemi", "Johnson",
            "Gonzalez", "Al-Rahman", "Patel", "Silva", "Okonkwo", "Kim", "Martinez",
            "Nguyen", "Petrov", "Cohen", "Kumar", "Li", "Thompson", "Yamamoto"
        ]

        locations = {
            "startup": ["San Francisco, CA", "Austin, TX", "New York, NY"],
            "midsize": ["San Francisco, CA", "New York, NY", "Chicago, IL", "Austin, TX"],
            "enterprise": ["San Francisco, CA", "New York, NY", "London, UK", "Singapore", "Tokyo, Japan"]
        }

        first_name = random.choice(first_names)
        last_name = random.choice(last_names)

        # Generate email with realistic domain
        domains = ["company.com", "techcorp.io", "enterprise.net", "organization.org"]
        email = f"{first_name.lower()}.{last_name.lower()}@{random.choice(domains)}"

        # Generate phone number
        area_code = random.choice(["415", "212", "512", "312", "408", "650"])
        phone = f"+1-{area_code}-{random.randint(100,999):03d}-{random.randint(1000,9999):04d}"

        # Generate employee number
        emp_prefix = {"startup": "EMP", "midsize": "MID", "enterprise": "ENT"}.get(org_size, "EMP")
        emp_number = f"{emp_prefix}-{random.randint(10000, 99999)}"

        # Generate manager name (also diverse)
        manager_first = random.choice(first_names)
        manager_last = random.choice(last_names)

        # Generate start date
        days_ago = random.randint(180, 1825)  # 6 months to 5 years
        start_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

        return {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "login": email,
            "mobilePhone": phone,
            "employeeNumber": emp_number,
            "manager": f"{manager_first} {manager_last}",
            "location": random.choice(locations.get(org_size, locations["midsize"])),
            "startDate": start_date,
            "division": department,
            "costCenter": f"{department[:3].upper()}-{random.randint(100, 999)}",
            "department": department,
            "title": title
        }

    def generate_group_name(
        self,
        industry: str,
        department: str,
        group_type: str = "department"
    ) -> str:
        """
        Generate realistic Okta group name based on context.

        Args:
            industry: Industry type (e.g., 'healthcare', 'technology')
            department: Department name (e.g., 'Engineering', 'Sales')
            group_type: Type of group - 'department', 'team', 'role', 'project', 'location'

        Returns:
            Generated group name string

        Example:
            >>> name = generator.generate_group_name(
            ...     industry='technology',
            ...     department='Engineering',
            ...     group_type='team'
            ... )
            >>> print(name)
            'Engineering - Platform Team'
        """
        industry_context = self.INDUSTRIES.get(industry.lower(), "General business")

        group_type_descriptions = {
            "department": "main department group",
            "team": "sub-team within the department",
            "role": "role-based access group (e.g., Managers, Individual Contributors)",
            "project": "project-based temporary group",
            "location": "office/location-based group"
        }

        prompt = f"""Generate a realistic Okta group name for a {industry_context}.

Context:
- Department: {department}
- Group Type: {group_type} ({group_type_descriptions.get(group_type, 'general group')})
- Industry: {industry_context}

Generate a professional group name that follows these patterns:
- Department groups: "{department}" or "{department} Department"
- Team groups: "{department} - [Team Name]" (e.g., "Engineering - Platform Team")
- Role groups: "[Role] - {department}" or just "[Role]" (e.g., "Senior Engineers", "Managers - Sales")
- Project groups: "Project - [Project Name]" or "[Project Name] Team"
- Location groups: "{department} - [Location]" or "[Location] Office"

The name should be:
- 2-6 words long
- Professional and clear
- Specific to the {industry} industry where relevant

Return ONLY the group name, nothing else."""

        try:
            response = self._call_claude(prompt, max_tokens=50)
            # Validate response
            if response and len(response) < 100 and not any(char in response for char in ['{', '}', '[', ']']):
                return response.strip()
        except Exception:
            pass  # Fall through to fallback

        # Fallback to template-based generation
        return self._generate_fallback_group_name(industry, department, group_type)

    def _generate_fallback_group_name(
        self,
        industry: str,
        department: str,
        group_type: str
    ) -> str:
        """Generate fallback group name using templates."""
        templates = {
            "department": [f"{department}", f"{department} Department", f"{department} Team"],
            "team": [
                f"{department} - Core Team",
                f"{department} - Platform Team",
                f"{department} - Infrastructure",
                f"{department} - Product Team"
            ],
            "role": [
                f"{department} Managers",
                f"Senior {department}",
                f"{department} Leads",
                f"{department} Individual Contributors"
            ],
            "project": [
                f"Project Alpha - {department}",
                f"{department} - Q4 Initiative",
                f"Innovation Team - {department}"
            ],
            "location": [
                f"{department} - San Francisco",
                f"{department} - Remote",
                f"{department} - East Coast"
            ]
        }

        options = templates.get(group_type, templates["department"])
        return random.choice(options)

    def generate_group_description(
        self,
        industry: str,
        group_name: str,
        group_type: str = "department"
    ) -> str:
        """
        Generate professional group description for Okta.

        Args:
            industry: Industry type
            group_name: Name of the group
            group_type: Type of group

        Returns:
            Generated group description string

        Example:
            >>> desc = generator.generate_group_description(
            ...     industry='technology',
            ...     group_name='Engineering - Platform Team',
            ...     group_type='team'
            ... )
            >>> print(desc)
            'Platform engineering team responsible for core infrastructure...'
        """
        industry_context = self.INDUSTRIES.get(industry.lower(), "General business")

        prompt = f"""Generate a concise, professional description for an Okta group in a {industry_context}.

Group Name: {group_name}
Group Type: {group_type}
Industry: {industry_context}

Create a 1-2 sentence description that:
- Explains the group's purpose and responsibilities
- Is specific to the {industry} industry
- Uses professional language
- Is informative but concise

Examples:
- "Platform engineering team responsible for core infrastructure and developer tools"
- "Sales representatives covering California, Oregon, and Washington territories"
- "ICU nursing staff at Memorial Hospital - San Francisco campus"
- "Managers across all engineering teams with approval and budget authority"

Return ONLY the description, nothing else."""

        response = self._call_claude(prompt, max_tokens=100)

        # Validate response
        if response and len(response) < 300:
            return response.strip()

        # Fallback
        fallback_descriptions = {
            "department": f"Department group for {group_name} team members and resources",
            "team": f"Specialized team within the organization focused on specific deliverables",
            "role": f"Role-based access group for managing permissions and responsibilities",
            "project": f"Project team collaborating on strategic initiatives",
            "location": f"Location-based group for regional coordination and resources"
        }
        return fallback_descriptions.get(group_type, f"Group for {group_name} in {industry} organization")

    def generate_profile_update_reason(
        self,
        update_type: str,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None
    ) -> str:
        """
        Generate realistic reason for user profile update.

        Args:
            update_type: Type of update - 'promotion', 'transfer', 'relocation', 'manager_change'
            old_value: Previous value (e.g., old title, old department)
            new_value: New value

        Returns:
            Generated update reason string

        Example:
            >>> reason = generator.generate_profile_update_reason(
            ...     update_type='promotion',
            ...     old_value='Software Engineer',
            ...     new_value='Senior Software Engineer'
            ... )
            >>> print(reason)
            'Promoted from Software Engineer to Senior Software Engineer'
        """
        update_contexts = {
            "promotion": f"title change from {old_value} to {new_value} (promotion)",
            "transfer": f"department transfer from {old_value} to {new_value}",
            "relocation": f"office relocation from {old_value} to {new_value}",
            "manager_change": f"reporting structure change to {new_value}"
        }

        context = update_contexts.get(update_type, "profile update")

        prompt = f"""Generate a brief, professional description for a user profile update.

Update Type: {update_type}
Context: {context}

Generate a 1-sentence description that would appear in an activity log.
Make it professional and informative.

Examples:
- "Promoted from Senior Engineer to Engineering Manager"
- "Transferred from Sales to Customer Success as part of reorganization"
- "Relocated from New York to Austin office"
- "Reporting structure changed - now reports to Sarah Johnson"
- "Role change due to internal mobility program"

Return ONLY the description, nothing else."""

        response = self._call_claude(prompt, max_tokens=80)

        # Validate and return
        if response and len(response) < 200:
            return response.strip()

        # Fallback
        fallbacks = {
            "promotion": f"Promoted from {old_value} to {new_value}",
            "transfer": f"Transferred from {old_value} to {new_value}",
            "relocation": f"Relocated from {old_value} to {new_value}",
            "manager_change": f"Reporting structure updated - now reports to {new_value}"
        }

        return fallbacks.get(update_type, "Profile updated")

    def generate_activity_description(
        self,
        activity_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate professional activity description for Okta logs.

        Args:
            activity_type: Type of activity - 'onboarding', 'offboarding', 'app_assignment',
                          'group_change', 'password_reset', 'mfa_enrollment'
            context: Additional context (e.g., user name, app name, group name)

        Returns:
            Generated activity description string

        Example:
            >>> desc = generator.generate_activity_description(
            ...     activity_type='onboarding',
            ...     context={'user': 'John Smith', 'department': 'Engineering'}
            ... )
            >>> print(desc)
            'New employee John Smith onboarded to Engineering department'
        """
        context = context or {}

        activity_contexts = {
            "onboarding": f"new employee {context.get('user', 'user')} joining {context.get('department', 'organization')}",
            "offboarding": f"employee {context.get('user', 'user')} leaving organization",
            "app_assignment": f"application {context.get('app', 'application')} assigned to {context.get('user', 'user')}",
            "group_change": f"user {context.get('user', 'user')} group membership change",
            "password_reset": f"password reset for {context.get('user', 'user')}",
            "mfa_enrollment": f"MFA enrollment for {context.get('user', 'user')}"
        }

        activity_context = activity_contexts.get(activity_type, "user activity")

        prompt = f"""Generate a professional activity log description for Okta.

Activity Type: {activity_type}
Context: {activity_context}

Create a brief, professional description (1 sentence) that would appear in an activity log.

Examples:
- "New employee John Smith onboarded to Engineering department with standard access provisioning"
- "User Sarah Johnson offboarded - all access revoked and account deactivated"
- "Salesforce application assigned to Maria Rodriguez as part of Sales team onboarding"
- "User added to 'Engineering - Platform Team' group for project collaboration"
- "Self-service password reset completed successfully"
- "Okta Verify MFA enrollment completed for enhanced security"

Return ONLY the description, nothing else."""

        response = self._call_claude(prompt, max_tokens=100)

        # Validate and return
        if response and len(response) < 200:
            return response.strip()

        # Fallback descriptions
        fallbacks = {
            "onboarding": f"New employee {context.get('user', 'user')} onboarded to {context.get('department', 'organization')}",
            "offboarding": f"Employee {context.get('user', 'user')} offboarded from organization",
            "app_assignment": f"Application {context.get('app', 'assigned')} to {context.get('user', 'user')}",
            "group_change": f"Group membership updated for {context.get('user', 'user')}",
            "password_reset": f"Password reset completed for {context.get('user', 'user')}",
            "mfa_enrollment": f"MFA enrollment completed for {context.get('user', 'user')}"
        }

        return fallbacks.get(activity_type, "User activity recorded")

    def validate_user_profile(self, profile: Dict[str, Any]) -> bool:
        """
        Validate generated user profile data.

        Args:
            profile: User profile dictionary

        Returns:
            True if profile is valid, False otherwise
        """
        # Check required fields
        required_fields = ["firstName", "lastName", "email", "login"]
        if not all(field in profile for field in required_fields):
            return False

        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, profile.get("email", "")):
            return False

        # Validate phone format if present
        if "mobilePhone" in profile:
            phone = profile["mobilePhone"]
            phone_pattern = r'^\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$'
            if not re.match(phone_pattern, phone.replace(" ", "")):
                return False

        # Validate date format if present
        if "startDate" in profile:
            try:
                datetime.strptime(profile["startDate"], '%Y-%m-%d')
            except ValueError:
                return False

        # Check name lengths
        if len(profile.get("firstName", "")) > 50 or len(profile.get("lastName", "")) > 50:
            return False

        return True


# Example usage
if __name__ == "__main__":
    # This is just for testing
    import sys

    if len(sys.argv) < 2:
        print("Usage: python llm_generator.py <ANTHROPIC_API_KEY>")
        sys.exit(1)

    generator = LLMGenerator(api_key=sys.argv[1])

    # Test project name generation
    print("=" * 60)
    print("Testing LLM Generator - Asana Methods")
    print("=" * 60)

    print("\nGenerating project name for Healthcare:")
    project_name = generator.generate_project_name("healthcare")
    print(f"  -> {project_name}")

    print("\nGenerating task name:")
    task_name = generator.generate_task_name("healthcare", project_name)
    print(f"  -> {task_name}")

    print("\nGenerating comment (starting work):")
    comment = generator.generate_comment_starting_work("Alice", task_name)
    print(f"  -> {comment}")

    print("\nGenerating comment (blocked):")
    blocked = generator.generate_comment_blocked("Alice", task_name, "healthcare")
    print(f"  -> {blocked}")

    # Test Okta methods
    print("\n" + "=" * 60)
    print("Testing LLM Generator - Okta Methods")
    print("=" * 60)

    print("\nGenerating user profile (Technology/Engineering):")
    profile = generator.generate_user_profile(
        industry="technology",
        department="Engineering",
        title="Senior Software Engineer",
        org_size="midsize"
    )
    if generator.validate_user_profile(profile):
        print(f"  Name: {profile.get('firstName')} {profile.get('lastName')}")
        print(f"  Email: {profile.get('email')}")
        print(f"  Title: {profile.get('title')}")
        print(f"  Manager: {profile.get('manager')}")
    else:
        print("  Invalid profile generated!")

    print("\nGenerating group name (Team):")
    group_name = generator.generate_group_name(
        industry="technology",
        department="Engineering",
        group_type="team"
    )
    print(f"  -> {group_name}")

    print("\nGenerating group description:")
    group_desc = generator.generate_group_description(
        industry="technology",
        group_name=group_name,
        group_type="team"
    )
    print(f"  -> {group_desc}")

    print("\nGenerating profile update reason (Promotion):")
    update_reason = generator.generate_profile_update_reason(
        update_type="promotion",
        old_value="Software Engineer",
        new_value="Senior Software Engineer"
    )
    print(f"  -> {update_reason}")

    print("\nGenerating activity description (Onboarding):")
    activity_desc = generator.generate_activity_description(
        activity_type="onboarding",
        context={
            "user": "John Smith",
            "department": "Engineering"
        }
    )
    print(f"  -> {activity_desc}")

    print("\nAPI Usage Stats:")
    stats = generator.get_usage_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
