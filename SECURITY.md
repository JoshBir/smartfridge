# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within SmartFridge, please send an email to security@example.com. All security vulnerabilities will be promptly addressed.

Please include the following information:

- Type of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

**Do not** open a public GitHub issue for security vulnerabilities.

## Security Measures

### Authentication

- **Password Requirements**
  - Minimum 8 characters
  - Must contain uppercase and lowercase letters
  - Must contain at least one digit
  - Must contain at least one special character
  
- **Password Storage**
  - bcrypt hashing with work factor 12
  - Passwords are never stored in plain text
  - Passwords are never logged

- **Session Management**
  - Secure, HttpOnly, SameSite cookies
  - Session timeout after 1 hour of inactivity
  - Session regeneration on login
  - Complete session destruction on logout

### Protection Against Common Attacks

#### Cross-Site Request Forgery (CSRF)
- All state-changing operations require CSRF tokens
- Tokens are validated server-side via Flask-WTF
- Tokens are rotated per session

#### Cross-Site Scripting (XSS)
- Content Security Policy headers via Flask-Talisman
- All user input is escaped in templates
- Jinja2 auto-escaping enabled by default

#### SQL Injection
- Parameterised queries via SQLAlchemy ORM
- No raw SQL queries with user input
- Input validation on all forms

#### Brute Force Attacks
- Rate limiting on login endpoint (5 requests/second)
- Account lockout after multiple failed attempts (recommended)
- CAPTCHA on registration (recommended for production)

### Security Headers

The following security headers are set via Flask-Talisman:

| Header | Value |
|--------|-------|
| Content-Security-Policy | Restrictive policy |
| X-Content-Type-Options | nosniff |
| X-Frame-Options | SAMEORIGIN |
| X-XSS-Protection | 1; mode=block |
| Strict-Transport-Security | max-age=31536000; includeSubDomains |
| Referrer-Policy | strict-origin-when-cross-origin |

### Data Protection

- **Database**
  - Sensitive fields are encrypted at rest (production)
  - Database connections use TLS (production)
  - Regular backups with encryption

- **User Data**
  - Users can only access their own data
  - Admin access is logged
  - Data export functionality available

### Production Recommendations

1. **Use HTTPS only** - Configure TLS certificates
2. **Enable HSTS** - Already configured via Flask-Talisman
3. **Use strong secrets** - Generate cryptographically random SECRET_KEY
4. **Database security** - Use PostgreSQL with strong passwords
5. **Regular updates** - Keep dependencies updated
6. **Monitoring** - Enable logging and alerting
7. **Backups** - Regular encrypted backups of database

### Security Checklist

Before deploying to production:

- [ ] Change default SECRET_KEY
- [ ] Use HTTPS with valid certificates
- [ ] Configure PostgreSQL with strong credentials
- [ ] Enable rate limiting
- [ ] Set up logging and monitoring
- [ ] Configure firewall rules
- [ ] Review CORS settings if applicable
- [ ] Test all authentication flows
- [ ] Run security scanner (Bandit)
- [ ] Review dependency vulnerabilities (Safety)

## Dependency Security

Regularly check for vulnerable dependencies:

```bash
# Check for known vulnerabilities
pip install safety
safety check

# Static security analysis
pip install bandit
bandit -r app/
```

## Security Updates

Security updates are released as soon as possible after a vulnerability is discovered. Users are encouraged to:

1. Watch this repository for releases
2. Subscribe to security advisories
3. Keep dependencies updated
4. Run `pip install --upgrade -r requirements.txt` regularly

## Contact

For security concerns, contact: security@example.com

For general questions, please use GitHub Issues.
