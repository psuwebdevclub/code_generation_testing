from flask import Flask, jsonify, request, abort

app = Flask(__name__)

# Mock database (in-memory for now)
inventory = []

# Helper function to find item by ID
def find_item(item_id):
    return next((item for item in inventory if item['id'] == item_id), None)

# 1. Create an item
@app.route('/items', methods=['POST'])
def create_item():
    if not request.json or 'name' not in request.json:
        abort(400, 'Name is required.')
    
    new_item = {
        'id': inventory[-1]['id'] + 1 if inventory else 1,
        'name': request.json['name'],
        'description': request.json.get('description', ""),
        'quantity': request.json.get('quantity', 0),
        'price': request.json.get('price', 0.0)
    }
    inventory.append(new_item)
    return jsonify(new_item), 201

# 2. Get all items
@app.route('/items', methods=['GET'])
def get_items():
    return jsonify(inventory), 200

# 3. Get a single item by ID
@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item = find_item(item_id)
    if item is None:
        abort(404, 'Item not found.')
    return jsonify(item), 200

# 4. Update an item by ID
@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = find_item(item_id)
    if item is None:
        abort(404, 'Item not found.')
    
    if not request.json:
        abort(400, 'Request body is required.')

    item['name'] = request.json.get('name', item['name'])
    item['description'] = request.json.get('description', item['description'])
    item['quantity'] = request.json.get('quantity', item['quantity'])
    item['price'] = request.json.get('price', item['price'])
    
    return jsonify(item), 200

# 5. Delete an item by ID
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = find_item(item_id)
    if item is None:
        abort(404, 'Item not found.')
    
    inventory.remove(item)
    return jsonify({'result': 'Item deleted successfully'}), 200

# Error handling
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': str(error)}), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': str(error)}), 400

# Main entry
if __name__ == '__main__':
    app.run(debug=True)
