from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from route_optimizer import RouteOptimizer
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Change this to a secure secret key
route_optimizer = RouteOptimizer()

# Mock database for users and items (replace with actual database in production)
users = {}
items = {
    'running_shoes': {
        'name': 'Premium Running Shoes',
        'price': 4999.00,
        'stock': 30,
        'discount': 10,
        'image': 'https://encrypted-tbn0.gstatic.com/shopping?q=tbn:ANd9GcRZXSTWY8B4E2BsAz9KmYgM5Pa-KtFkYHgSfn4N53qSwqkZN4UGo47IlinNrg-t1N-lPYUsvyNiArpCL4q6zGY2n7-u_cXXw0onv2uCbWyhR1Z58i5mQ3lcZw',
        'category': 'Shoes',
        'description': 'High-quality running shoes for professional athletes'
    },
    'casual_sneakers': {
        'name': 'Casual Sneakers',
        'price': 2999.00,
        'stock': 40,
        'discount': 15,
        'image': 'https://encrypted-tbn2.gstatic.com/shopping?q=tbn:ANd9GcTDq1S9LdK2rEWxUui1vHkvbGneThvTlaT4x07SFkTSD6L015hef7mWVawe_npHMdE0JR9SDJlT3qyKY4pGp1JAsSBBu6Pd-IB-JLUIgOOPTEmihvbCWNMvyw',
        'category': 'Shoes',
        'description': 'Comfortable everyday casual sneakers'
    },
    'formal_shoes': {
        'name': 'Classic Formal Shoes',
        'price': 3999.00,
        'stock': 25,
        'discount': 5,
        'image': 'https://encrypted-tbn1.gstatic.com/shopping?q=tbn:ANd9GcTCbCXIzLCqDvs0gBQm0FTDEjjoa1UsgNjgpyw4tvJLCgApvgJXJJEec4HjRniGo2ff9KcVEicWqsETUh8EMVy4zeZGSfYwUcPbK77ejZJyJ8Wc2D_xvgrV',
        'category': 'Shoes',
        'description': 'Elegant formal shoes for professional occasions'
    },
    'smartphone': {
        'name': 'Latest Smartphone Model',
        'price': 49999.00,
        'stock': 20,
        'discount': 12,
        'image': 'https://m.media-amazon.com/images/I/719PYirSevL.jpg',
        'category': 'Electronics',
        'description': 'Feature-rich smartphone with advanced camera system'
    },
    'laptop': {
        'name': 'Professional Laptop',
        'price': 69999.00,
        'stock': 15,
        'discount': 8,
        'image': 'https://images.pexels.com/photos/205421/pexels-photo-205421.jpeg?auto=compress&cs=tinysrgb&dpr=1&w=500',
        'category': 'Electronics',
        'description': 'High-performance laptop for work and entertainment'
    },
    'headphones': {
        'name': 'Premium Wireless Headphones',
        'price': 24999.00,
        'stock': 35,
        'discount': 20,
        'image': 'https://store.storeimages.cdn-apple.com/4668/as-images.apple.com/is/MQTQ3?wid=1377&hei=2057&fmt=jpeg&qlt=95&.v=1741643688229',
        'category': 'Electronics',
        'description': 'High-quality wireless headphones with noise cancellation'
    },
    'tshirt': {
        'name': 'Casual T-Shirt',
        'price': 999.00,
        'stock': 50,
        'discount': 10,
        'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTAG6_6rQi9pvzoV0PsDPWGf7fCEwkRwdqrpA&s',
        'category': 'Clothing',
        'description': 'Comfortable cotton t-shirt for daily wear'
    },
    'jeans': {
        'name': 'Classic Denim Jeans',
        'price': 2499.00,
        'stock': 45,
        'discount': 15,
        'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRJS3OgBMDZnfSn9LX5PlxSgI_vw6s51RH0Fw&s',
        'category': 'Clothing',
        'description': 'Classic fit denim jeans with authentic styling'
    },
    'jacket': {
        'name': 'Stylish Jacket',
        'price': 3499.00,
        'stock': 30,
        'discount': 18,
        'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQuzzyXftV7C3R8UtcRtSLgnNT8j9MkdOVckw&s',
        'category': 'Clothing',
        'description': 'Trendy jacket for all seasons'
    }
}
# Remove the extra closing brace as it's not needed

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if email in users and check_password_hash(users[email]['password'], password):
        session['user_id'] = email
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid email or password'}), 401

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if email in users:
        return jsonify({'error': 'Email already registered'}), 400
    
    users[email] = {
        'name': name,
        'password': generate_password_hash(password),
        'cart': []
    }
    
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/get-items')
def get_items():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(items)

@app.route('/get-deals')
def get_deals():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    deals = {k: v for k, v in items.items() if v['discount'] > 0}
    return jsonify(deals)

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity', 1)
    
    if item_id not in items or items[item_id]['stock'] < quantity:
        return jsonify({'error': 'Item not available'}), 400
    
    user = users[session['user_id']]
    user['cart'].append({'item_id': item_id, 'quantity': quantity})
    items[item_id]['stock'] -= quantity
    
    return jsonify({'success': True, 'cart_count': len(user['cart'])})

@app.route('/cart/get')
def get_cart():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = users[session['user_id']]
    cart_items = []
    total = 0
    
    for cart_item in user['cart']:
        item = items[cart_item['item_id']]
        price = item['price'] * (1 - item['discount']/100)
        cart_items.append({
            'name': item['name'],
            'quantity': cart_item['quantity'],
            'price': price,
            'total': price * cart_item['quantity']
        })
        total += price * cart_item['quantity']
    
    return jsonify({
        'items': cart_items,
        'total': total
    })

@app.route('/submit-order', methods=['POST'])
def submit_order():
    data = request.get_json()
    location = data.get('location')
    items = data.get('items')
    
    if not location or not items:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Create a simple order object
    order = type('Order', (), {'location': location})()
    
    # Optimize route for the order
    try:
        route = route_optimizer.optimize_routes([order])
        route_optimizer.assign_orders([order])
        
        return jsonify({
            'status': 'success',
            'message': 'Order submitted successfully',
            'route': route
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-locations')
def get_locations():
    locations = list(route_optimizer.delivery_locations.keys())
    locations.remove('Warehouse')  # Don't show warehouse as delivery option
    return jsonify(locations)

if __name__ == '__main__':
    app.run(debug=True)