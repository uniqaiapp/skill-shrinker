# Security

This project is a single Python script with no dependencies. The only network call it can make is `POST https://api.anthropic.com/v1/messages/count_tokens`, and only when `ANTHROPIC_API_KEY` is set and `--tokens` is `auto` or `api`. The file contents are sent in that request; use `--tokens estimate` for files you do not want to leave the machine.

To report a vulnerability, email support@uniqai.app with "security" in the subject. Do not open a public issue for it. You will get an acknowledgement, and a fix or a statement within a reasonable time.
