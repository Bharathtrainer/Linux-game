# Enterprise Linux Mastery Game

## Setup
1. Set NIM_BASE_URL and NIM_API_KEY as environment variables
2. Build sandbox: docker build -t linux-mastery-sandbox sandbox/
3. Run backend: uvicorn backend.main:app --reload
