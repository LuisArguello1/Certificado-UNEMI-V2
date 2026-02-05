import secrets
from django.utils.deprecation import MiddlewareMixin

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware para centralizar cabeceras de seguridad y CSP.
    Genera un nonce único por petición para permitir inline-scripts seguros.
    """
    def process_request(self, request):
        # Generar un nonce único para esta solicitud
        # Se usará en los templates vía context_processor
        request.csp_nonce = secrets.token_hex(16)

    def process_response(self, request, response):
        nonce = getattr(request, 'csp_nonce', '')
        
        # 1. Definir Content-Security-Policy (CSP)
        # - default-src: Bloquea todo por defecto
        # - script-src: Permite self, scripts con el nonce actual, y CDNs de confianza
        # - style-src: Permite self, estilos inline (necesario para Tailwind/Alpine) y CDNs
        # - img-src: Permite imagenes locales y data URIs
        # - frame-ancestors: Solo permite ser embebido por el mismo origen
        csp_elements = [
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.tailwindcss.com https://code.jquery.com https://cdn.ckeditor.com",
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com",
            "font-src 'self' https://cdnjs.cloudflare.com https://fonts.gstatic.com",
            "img-src 'self' data: blob: https://*.trycloudflare.com",
            "frame-ancestors 'self'",
            "connect-src 'self' https://*.trycloudflare.com https://cdn.jsdelivr.net https://cdn.ckeditor.com"
        ]
        csp_policy = "; ".join(csp_elements)
        
        # Solo aplicar CSP a respuestas HTML para evitar overhead en estáticos/JSON
        content_type = response.get('Content-Type', '')
        if 'text/html' in content_type:
            response['Content-Security-Policy'] = csp_policy
            
        # 2. X-Content-Type-Options: Previene que el navegador "divine" el MIME type
        response['X-Content-Type-Options'] = 'nosniff'
        
        # 3. X-Frame-Options: Previene ataques de Clickjacking (Clickjacking Protection)
        if not response.get('X-Frame-Options'):
            response['X-Frame-Options'] = 'SAMEORIGIN'
            
        # 4. Referrer-Policy: Controla cuánta info se envía al navegar a otros sitios
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
