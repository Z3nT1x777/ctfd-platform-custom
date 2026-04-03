# Simple Login Challenge

## Overview

**Category:** Web  
**Difficulty:** Easy (Warmup)  
**Points:** 50  

A basic web login form challenge for CTF practice. Test your authentication skills.

## Challenge Description

Access a simple Flask web application with a login form. Authenticate with the correct credentials to obtain the flag.

### Objective
- Find the correct username and password
- Login successfully
- Capture the flag displayed on the authenticated page

### Flag Format
```
FLAG{...}
```

## Deployment

### Quick Start (Local Docker)

```bash
docker-compose up -d
curl http://localhost:5000
```

### With Orchestrator

The orchestrator API can spawn per-team instances:

```bash
# Start instance for team 1
curl -X POST \
  -H "X-Orchestrator-Token: ChangeMe-Orchestrator-Token" \
  -H "X-Signature-Timestamp: $(date +%s)" \
  -H "X-Signature: <signature>" \
  http://127.0.0.1:8181/start \
  -d '{"team_id": "1", "challenge": "simple-login"}'

# Response includes port:
# {"ok": true, "port": 5001, "url": "http://vm:5001"}
```

## Solution (For CTF Organizers)

### Credentials

Default users in `app.py`:
- Username: `admin`
- Password: `Ch4ll3ng3Password!`

Alternative:
- Username: `player`
- Password: `PlayerPass123`

### Steps

1. Access the challenge URL
2. Enter username: `admin` and password: `Ch4ll3ng3Password!`
3. Click "Login"
4. Flag is displayed on successful authentication
5. Submit flag to CTF platform

### Vulnerability (Educational)

The app is vulnerable to note SQL injection (for learning purposes):
- Try: `admin' --` in username field
- This demonstrates basic SQL injection (though this simple version uses plain Python dicts, not actual SQL)

## Files

- `app.py` - Flask application with login form
- `requirements.txt` - Python dependencies (Flask)
- `Dockerfile` - Container image definition
- `docker-compose.yml` - Local deployment configuration
- `challenge.yml` - CTF platform metadata
- `flag.txt` - Challenge flag (for reference)

## Environment Variables

When deploying via orchestrator:

```bash
FLASK_ENV=production
FLAG=FLAG{Authentification_B4sique_CTF}
SECRET_KEY=<random-session-key>
```

## Customization

### Change the Flag

Edit `app.py` line 16:
```python
FLAG = os.environ.get("FLAG", "FLAG{Your_Custom_Flag_Here}")
```

Or set environment variable:
```bash
docker-compose -e FLAG="FLAG{custom}" up
```

### Add More Users

Edit `app.py` line 19:
```python
USERS = {
    "admin": "password1",
    "player": "password2",
    "newuser": "password3",
}
```

### Change Difficulty / Points

Edit `challenge.yml`:
```yaml
difficulty: Medium
points: 150
```

## Troubleshooting

### Port Already in Use

If port 5000 is already in use:

```bash
# Use different port in docker-compose.yml
ports:
  - "5001:5000"  # Change from 5000 to 5001
```

### Application Won't Start

```bash
# Check logs
docker-compose logs simple-login

# Rebuild without cache
docker-compose build --no-cache
```

### Flag Not Displaying

1. Verify login was successful (should show "Welcome" message)
2. Check environment variable:
   ```bash
   docker-compose exec simple-login env | grep FLAG
   ```

## Docker Commands

```bash
# Build image
docker build -t ctf-simple-login .

# Run container
docker run -p 5000:5000 -e FLAG="FLAG{test}" ctf-simple-login

# Docker-compose
docker-compose up --build
docker-compose down
docker-compose logs -f

# View running containers
docker ps | grep simple-login
```

## Security Notes

⚠️ **This is a learning challenge. In production:**
- Use actual database (not hardcoded users)
- Hash passwords (not plaintext)
- Implement HTTPS (not HTTP)
- Add input validation / sanitization
- Use parameterized queries (not string concatenation)
- Implement rate limiting on login attempts

## References

- Flask Documentation: https://flask.palletsprojects.com/
- OWASP Top 10: https://owasp.org/Top10/
- SQL Injection: https://owasp.org/www-community/attacks/SQL_Injection
