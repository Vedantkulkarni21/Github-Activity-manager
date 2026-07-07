## AI Tools Used

I used ChatGPT (GPT-5.5) and Claude throughout development. AI was used as an engineering assistant for implementation ideas, debugging, API usage, deployment, and code review. All code was reviewed, modified, and tested manually before being used.

## Key Decisions I Made

- Built a configurable rule engine instead of hardcoded automation so users can define their own conditions and actions.
- Used background processing for webhook events so GitHub receives an immediate response while actions execute asynchronously.
- Encrypted GitHub access tokens before storing them in the database.

## Hardest Bug

The biggest challenge was deploying OAuth from localhost to Render and Vercel. Authentication initially failed because of cookie settings, callback URLs, and environment configuration. After debugging browser requests and server logs, I updated the production callback URL and cookie configuration (`Secure=True`, `SameSite=None`), which resolved the issue.

## What I'd Improve

- AI-powered issue summarization using Gemini
- More advanced rule conditions
- WebSocket-based live event updates
- GitHub App authentication instead of an OAuth App

## Example Prompt

> "Review my GitHub webhook processing flow and suggest improvements for security, retries, idempotency, and background processing."

The suggestions helped improve the reliability of the webhook processing pipeline.