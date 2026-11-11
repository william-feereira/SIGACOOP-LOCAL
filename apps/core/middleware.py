class SecurityHeadersMiddleware:
    """Cabeçalhos de segurança que o Django 5.2 não define sozinho (CSP e Permissions-Policy)."""
    CSP = "; ".join([
        "default-src 'self'", "script-src 'self'", "style-src 'self'", "img-src 'self' data:",
        "font-src 'self'", "connect-src 'self'", "form-action 'self'", "frame-ancestors 'none'",
        "base-uri 'self'", "object-src 'none'",
    ])

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault("Content-Security-Policy", self.CSP)
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        return response
