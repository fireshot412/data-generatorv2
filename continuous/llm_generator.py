#!/usr/bin/env python3
"""
LLM Generator for creating realistic Asana content using Claude API.
Generates industry-specific project names, task names, comments, and more.
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
import anthropic


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
            # First comment - use starter template
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

            # Build conversation history string
            conversation_history = "\n".join([
                f"- {c.get('user', 'Unknown')}: \"{c.get('comment', '')}\""
                for c in existing_comments[-3:]  # Last 3 comments for context
            ])

            prompt = f"""Generate a natural follow-up comment from {user_name} on task: "{task_name}"
Context: {industry_context}
Project: {project_name}

Recent conversation history:
{conversation_history}

Last comment was from {last_commenter}: "{last_comment_text}"

CRITICAL: The comment MUST use a DIFFERENT opening phrase than any previous comment. Generate a contextual response that:
- Uses a UNIQUE opening phrase (avoid "Sounds good", "Thanks", "Great" if already used)
- Moves the conversation forward naturally
- Is 1-2 sentences
- Sounds like real workplace communication

VARY your opening approach - use different structures:
- Acknowledgement: "Got it, I'll...", "Understood, will...", "Makes sense, I can..."
- Direct action: "I'll review...", "Let me...", "Working on..."
- Question/offer: "Need any help with...", "Want me to...", "Should I..."
- Status update: "I've already...", "Just finished...", "Almost done with..."
- Simple confirmation: "Done.", "On it.", "Will do."

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
    print("Testing LLM Generator")
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

    print("\nAPI Usage Stats:")
    stats = generator.get_usage_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
