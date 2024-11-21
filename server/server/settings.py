import os

# MongoDB Configuration
MONGO_SERVER_URL = os.environ.get(
    "MONGO_SERVER_URL", "mongodb://localhost:27017"
)
MONGO_USERNAME = os.environ.get("MONGO_USERNAME", "root")
MONGO_PASSWORD = os.environ.get("MONGO_PASSWORD", "example")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "mydb")

# Data Storage Path
DATA_STORAGE_PATH = os.environ.get("DATA_STORAGE_PATH", "storage")

# Additional MongoDB settings (if needed)
MONGO_AUTH_SOURCE = os.environ.get("MONGO_AUTH_SOURCE", "admin")
MONGO_AUTH_MECHANISM = os.environ.get("MONGO_AUTH_MECHANISM", "SCRAM-SHA-256")

# Construct MongoDB URI
MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_SERVER_URL}/{MONGO_DB_NAME}?authSource={MONGO_AUTH_SOURCE}&authMechanism={MONGO_AUTH_MECHANISM}"  # noqa

# LLM_PROVIDER
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")