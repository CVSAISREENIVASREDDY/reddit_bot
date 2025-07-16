import json
import google.generativeai as genai
from scrap import main    

class RedditPersonaAnalyzer:
    """
    Encapsulates loading a user’s Reddit data, configuring Gemini,
    generating structured responses, and packaging results.
    """

    def __init__(self, username: str, api_key: str):
        self.username = username
        self.api_key = api_key.strip()

        if not self.api_key:
            raise ValueError("API key is required. Please set the API key before using the model.")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash-latest")
        self.posts, self.comments = self._load_data()


    def _load_data(self):
        posts, comments = main(self.username)
        return posts, comments

    def _generate_response(self, prompt: str) -> str:
        """
        Feed posts + comments into Gemini with the caller‑supplied question.
        Returns raw text from the model (stripped).
        """
        full_prompt = f"""
        You are a helpful assistant, your task is first to study the following text
        and then answer the question based on the text.
        The text I will provide is the posts and comments of a social media platform, Reddit.
        The text is in the form of a list of dictionaries.
        Each dictionary contains different fields of the post or comment.
        If the value of a field is Unknown it means that the field is not available.

        The posts and comments are as follows:
        {self.posts}, {self.comments}

        {prompt}
        return the response in a list format,
        do not include any explanation or additional text; each element of the list should be
        a single behavior or habit of the user,
        do not include any numbers or bullet points, just the behaviors and habits in a list format.
        each element of the list should be a single line or two lines at most,
        give me a max of 10 elements in the list,
        """
        response = self.model.generate_content(full_prompt)
        return response.text.strip()

    def build_persona(self) -> dict:
        """Return the composite dictionary of goals, frustrations, interests, motivations, and fears."""
        return {
            "goals": self._generate_response(
                "Give me a list of the goals and aspirations of the user based on the posts and comments."
            ).split("\n"),
            "frustrations": self._generate_response(
                "Give me a list of the frustrations and challenges of the user based on the posts and comments."
            ).split("\n"),
            "interests": self._generate_response(
                "Give me a list of the interests and hobbies of the user based on the posts and comments."
            ).split("\n"),
            "motivations": self._generate_response(
                "Give me a list of the motivations along with the percentage of motivations of the user based on the posts and comments."
            ).split("\n"),
            "fears": self._generate_response(
                "Give me a list of the fears and concerns of the user based on the posts and comments."
            ).split("\n"),
        }
