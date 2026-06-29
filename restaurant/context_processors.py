"""
Global context processor — injects cart_count into every template.
"""


def cart_count(request):
    cart = request.session.get('cart', {})
    total = sum(cart.values()) if cart else 0
    return {'cart_count': total}
