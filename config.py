from decouple import config

#groq 
GROQ_API_KEY = config("GROQ_API_KEY")
GROQ_MODEL_NAME = config("GROQ_MODEL_NAME")

#cal.com
CALCOM_KEY = config("CALCOM_KEY")
CALCOM_EVENT = config("CALCOM_EVENT")

#redis URL
REDIS_URL = config("REDIS_URL")

#postgres URL
DATABASE_URL=config("DATABASE_URL")
