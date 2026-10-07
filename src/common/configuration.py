from dotenv import load_dotenv
import os

load_dotenv()

MAX_CONSECUTIVE_ERRORS: int = int(os.getenv("MAX_CONSECUTIVE_ERRORS", "3"))
