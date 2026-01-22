"""LLM-powered profile interview system."""

import json
import logging
import os
from typing import Optional

from openai import AsyncOpenAI

from src.profile.models import (
    UserProfile,
    CitizenshipStatus,
    DegreeLevel,
    YearInSchool,
    Gender,
)

logger = logging.getLogger(__name__)

# System prompt for the interview
SYSTEM_PROMPT = """You are a friendly scholarship advisor helping a student build their profile for scholarship matching. Your goal is to gather information about them through natural conversation.

You need to collect information about:
1. Academic: GPA, major, minor, year in school, institution
2. Location: Country of origin, state, citizenship status
3. Demographics: Ethnicity, gender, first-generation status
4. Financial: Income bracket, financial need
5. Interests: Career goals, activities, volunteer work
6. Affiliations: Organizations, clubs, military/religious affiliations

Guidelines:
- Ask 2-3 related questions at a time, not all at once
- Be conversational and encouraging
- Accept partial information - don't pressure for everything
- After 4-5 exchanges, summarize what you've learned and ask if anything is missing
- When you have enough info (or user indicates they're done), output the final profile

When ready to output the profile, respond with EXACTLY this format:
[PROFILE_COMPLETE]
```json
{
  "name": "...",
  "academic": {"gpa": ..., "major": "...", ...},
  "location": {"citizenship_status": "...", "state": "...", ...},
  "demographics": {"ethnicity": [...], "first_generation": ..., ...},
  "financial": {"financial_need": ..., ...},
  "interests": {"career_goals": [...], "activities": [...], ...},
  "affiliations": {"organizations": [...], ...}
}
```

Use null for unknown fields. For enums use: 
- citizenship_status: us_citizen, permanent_resident, international, daca, refugee, other
- degree_level: high_school, undergraduate, graduate, doctoral, professional
- year_in_school: freshman, sophomore, junior, senior, fifth_year, graduate_1, graduate_2, graduate_3_plus
- gender: male, female, non_binary, other, prefer_not_to_say
"""

INITIAL_MESSAGE = """Hi! I'm here to help you find scholarships that match your profile. I'll ask you a few questions to understand your background better.

Let's start with the basics - what's your name, and can you tell me about your current academic situation? (What are you studying, what year are you in, and what's your approximate GPA?)"""


class ProfileInterviewer:
    """Conducts an LLM-powered interview to build a user profile."""

    def __init__(self, api_key: Optional[str] = None, draft_path: Optional[str] = None):
        """Initialize the interviewer.

        Args:
            api_key: OpenAI API key. If not provided, uses OPENAI_API_KEY env var.
            draft_path: Optional path for saving/loading interview drafts.
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable."
            )

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.conversation_history: list[dict] = []
        self.max_turns = 10  # Maximum conversation turns before forcing completion
        self.draft_path = draft_path or "data/interview_draft.json"
        self.auto_save = True  # Auto-save after each turn

    def reset(self) -> None:
        """Reset the conversation history."""
        self.conversation_history = []

    def save_draft(self) -> None:
        """Save conversation history to draft file."""
        try:
            with open(self.draft_path, "w") as f:
                json.dump({
                    "conversation_history": self.conversation_history,
                    "saved_at": __import__("datetime").datetime.now().isoformat(),
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save interview draft: {e}")

    def load_draft(self) -> bool:
        """Load conversation history from draft file.

        Returns:
            True if draft was loaded successfully.
        """
        try:
            if not os.path.exists(self.draft_path):
                return False

            with open(self.draft_path, "r") as f:
                data = json.load(f)

            self.conversation_history = data.get("conversation_history", [])
            return True
        except Exception as e:
            logger.warning(f"Failed to load interview draft: {e}")
            return False

    def clear_draft(self) -> None:
        """Remove the draft file if it exists."""
        try:
            if os.path.exists(self.draft_path):
                os.remove(self.draft_path)
        except Exception as e:
            logger.warning(f"Failed to clear interview draft: {e}")

    def draft_exists(self) -> bool:
        """Check if an interview draft exists."""
        return os.path.exists(self.draft_path)

    def get_initial_message(self) -> str:
        """Get the initial interview message."""
        return INITIAL_MESSAGE

    async def process_response(self, user_message: str) -> tuple[str, Optional[UserProfile]]:
        """Process a user response and generate the next question or final profile.

        Args:
            user_message: The user's response.

        Returns:
            Tuple of (assistant_message, profile_or_none).
            If profile is not None, the interview is complete.
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        # Check if we should force completion
        force_complete = len(self.conversation_history) >= self.max_turns * 2

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *self.conversation_history,
        ]

        if force_complete:
            messages.append({
                "role": "system",
                "content": "The interview has gone on long enough. Please output [PROFILE_COMPLETE] with the JSON profile based on what you've learned so far.",
            })

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )

            assistant_message = response.choices[0].message.content or ""

            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message,
            })

            # Check if profile is complete
            if "[PROFILE_COMPLETE]" in assistant_message:
                profile = self._extract_profile(assistant_message)
                return assistant_message, profile

            return assistant_message, None

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise

    async def process_response_streaming(self, user_message: str):
        """Process a user response with streaming output.

        Args:
            user_message: The user's response.

        Yields:
            Tuples of (chunk_type, content) where:
            - ("chunk", str): A text chunk from the response
            - ("done", (full_message, profile_or_none)): Final result
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
        })

        # Check if we should force completion
        force_complete = len(self.conversation_history) >= self.max_turns * 2

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            *self.conversation_history,
        ]

        if force_complete:
            messages.append({
                "role": "system",
                "content": "The interview has gone on long enough. Please output [PROFILE_COMPLETE] with the JSON profile based on what you've learned so far.",
            })

        try:
            stream = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                stream=True,
            )

            full_message = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_message += content
                    yield ("chunk", content)

            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": full_message,
            })

            # Check if profile is complete
            profile = None
            if "[PROFILE_COMPLETE]" in full_message:
                profile = self._extract_profile(full_message)
                # Clear draft on successful completion
                self.clear_draft()

            # Auto-save after each turn
            if self.auto_save:
                self.save_draft()

            # Yield final result
            yield ("done", (full_message, profile))

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise

    async def extract_partial_profile(self) -> Optional[UserProfile]:
        """Extract a partial profile from the current conversation.

        Useful for saving progress during an interview.

        Returns:
            UserProfile with whatever information could be extracted, or None.
        """
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT + "\n\nExtract a PARTIAL profile from the conversation so far. Output [PROFILE_COMPLETE] with the JSON immediately. Use null for unknown fields.",
            },
            *self.conversation_history,
        ]

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
            )

            assistant_message = response.choices[0].message.content or ""
            return self._extract_profile(assistant_message)

        except Exception as e:
            logger.warning(f"Failed to extract partial profile: {e}")
            return None

    def _extract_profile(self, message: str) -> Optional[UserProfile]:
        """Extract profile from the completion message.

        Args:
            message: The assistant message containing [PROFILE_COMPLETE] and JSON.

        Returns:
            UserProfile if extraction successful, None otherwise.
        """
        try:
            # Find JSON block
            start = message.find("```json")
            end = message.find("```", start + 7)

            if start == -1 or end == -1:
                # Try without code block markers
                start = message.find("{")
                end = message.rfind("}") + 1

            if start == -1 or end <= start:
                logger.error("Could not find JSON in profile completion message")
                return None

            json_str = message[start:end]
            if json_str.startswith("```json"):
                json_str = json_str[7:]

            data = json.loads(json_str)

            # Convert enum strings to enum values where needed
            if "location" in data and "citizenship_status" in data["location"]:
                cs = data["location"]["citizenship_status"]
                if cs and isinstance(cs, str):
                    try:
                        data["location"]["citizenship_status"] = CitizenshipStatus(cs)
                    except ValueError:
                        data["location"]["citizenship_status"] = None

            if "academic" in data:
                if "degree_level" in data["academic"]:
                    dl = data["academic"]["degree_level"]
                    if dl and isinstance(dl, str):
                        try:
                            data["academic"]["degree_level"] = DegreeLevel(dl)
                        except ValueError:
                            data["academic"]["degree_level"] = None

                if "year_in_school" in data["academic"]:
                    ys = data["academic"]["year_in_school"]
                    if ys and isinstance(ys, str):
                        try:
                            data["academic"]["year_in_school"] = YearInSchool(ys)
                        except ValueError:
                            data["academic"]["year_in_school"] = None

            if "demographics" in data and "gender" in data["demographics"]:
                g = data["demographics"]["gender"]
                if g and isinstance(g, str):
                    try:
                        data["demographics"]["gender"] = Gender(g)
                    except ValueError:
                        data["demographics"]["gender"] = None

            return UserProfile.model_validate(data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse profile JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to create profile from data: {e}")
            return None

    async def quick_extract(self, text: str) -> Optional[UserProfile]:
        """Extract profile from a single text description without conversation.

        Useful for importing existing profile data or testing.

        Args:
            text: Text description of the user's profile.

        Returns:
            UserProfile if extraction successful, None otherwise.
        """
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT + "\n\nExtract a profile from the following text and output [PROFILE_COMPLETE] with the JSON immediately.",
            },
            {
                "role": "user",
                "content": text,
            },
        ]

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
            )

            assistant_message = response.choices[0].message.content or ""
            return self._extract_profile(assistant_message)

        except Exception as e:
            logger.error(f"Error in quick_extract: {e}")
            return None
