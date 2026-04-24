from .models import Cart


def cart_count(request):
    """Add cart item count to all templates"""
    count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.filter(user=request.user, is_active=True).first()
            if cart:
                count = cart.get_items_count()
        except:
            pass
    return {'cart_items_count': count}
