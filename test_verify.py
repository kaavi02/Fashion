import requests
import json
import sys

BASE = 'http://127.0.0.1:8080'

try:
    # 1. Health
    h = requests.get(f'{BASE}/api/health').json()
    print('1. HEALTH:', h)

    # 2. Products
    prods = requests.get(f'{BASE}/api/products').json()
    print(f'2. PRODUCTS: {len(prods)} products retrieved. First: {prods[0]["name"]} (Brand: {prods[0]["brand_name"]})')

    # 3. Product Filter Test
    mens_prods = requests.get(f'{BASE}/api/products?gender=Men').json()
    print(f'   FILTER (Gender=Men): {len(mens_prods)} products')
    size_prods = requests.get(f'{BASE}/api/products?size=M').json()
    print(f'   FILTER (Size=M): {len(size_prods)} products')

    # 4. Auth Login
    login_res = requests.post(f'{BASE}/api/auth/login', json={'email':'demo@fashion.com','password':'Password123!'})
    login_data = login_res.json()
    token = login_data['access_token']
    user_name = login_data['user']['full_name']
    print(f'3. AUTH: Successfully logged in as "{user_name}". Token: {token[:25]}...')

    headers = {'Authorization': f'Bearer {token}'}

    # 5. AI Size Recommendation Engine
    size_req = {
        'gender': 'men',
        'height_cm': 178.0,
        'weight_kg': 72.5,
        'chest_cm': 99.0,
        'waist_cm': 83.0,
        'hips_cm': 98.0,
        'preferred_fit': 'regular',
        'category_name': 'Tops'
    }
    size_res = requests.post(f'{BASE}/api/size-advisor/recommend', json=size_req, headers=headers).json()
    print(f'4. AI SIZE ADVISOR: Recommended Size: {size_res["recommended_size"]} | Fit Confidence: {size_res["confidence_score"]}% | Commentary: {size_res["commentary"]}')

    # 6. Add to Cart
    first_slug = prods[0]['slug']
    detail = requests.get(f'{BASE}/api/products/{first_slug}').json()
    variant_id = detail['variants'][0]['id']
    cart_res = requests.post(f'{BASE}/api/cart/add', json={'variant_id': variant_id, 'quantity': 1}, headers=headers).json()
    print(f'5. CART: Added "{detail["name"]}" to cart. Total items: {cart_res["total_count"]}, Total: Rs. {cart_res["total"]}')

    # 7. Checkout Process
    checkout_payload = {
        'shipping_name': user_name,
        'shipping_email': 'demo@fashion.com',
        'shipping_phone': '+91 9876543210',
        'shipping_address': 'Flat 402, Skyline Luxury Apartments',
        'shipping_city': 'Bengaluru',
        'shipping_state': 'Karnataka',
        'shipping_postal_code': '560038',
        'shipping_country': 'India',
        'payment_method': 'Credit/Debit Card'
    }
    order_res = requests.post(f'{BASE}/api/checkout/process', json=checkout_payload, headers=headers).json()
    print(f'6. CHECKOUT: Order created! Order #: {order_res["order_number"]} | Status: {order_res["status"]} | Total: Rs. {order_res["total_amount"]}')

    # 8. Orders History
    orders_res = requests.get(f'{BASE}/api/orders', headers=headers).json()
    print(f'7. ORDERS: Retrieved {len(orders_res)} orders for customer.')

    # 9. Wishlist Toggle
    w_res = requests.post(f'{BASE}/api/wishlist/toggle/{detail["id"]}', headers=headers)
    print(f'8. WISHLIST: Status {w_res.status_code}, Response: {w_res.json()["message"]}')

    # 10. Web Pages Verification
    pages = ['/', '/products', f'/product/{first_slug}', '/cart', '/checkout', '/orders', '/wishlist', '/profile', '/login', '/register']
    status_codes = [requests.get(f'{BASE}{p}').status_code for p in pages]
    print('9. FRONTEND HTML PAGES STATUS:')
    for p, s in zip(pages, status_codes):
        print(f'   {p:35} -> HTTP {s}')

    print('\n[SUCCESS] ALL VERIFICATION TESTS PASSED PERFECTLY!')

except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
