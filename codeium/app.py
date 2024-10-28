"""
create a flask app file that has endpoints to manage a full scale inventory management system
"""

from flask import Flask, jsonify, request

app = Flask(__name__)

# Sample in-memory data store (replace with a database in a real application)
products = [
    {"id": 1, "name": "Product 1", "description": "This is product 1", "price": 10.99, "stock_level": 100},
    {"id": 2, "name": "Product 2", "description": "This is product 2", "price": 9.99, "stock_level": 50},
    {"id": 3, "name": "Product 3", "description": "This is product 3", "price": 12.99, "stock_level": 200},
]

orders = []

# Endpoint to get all products
@app.route("/products", methods=["GET"])
def get_products():
    return jsonify(products)

# Endpoint to get a single product by ID
@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(product)

# Endpoint to create a new product
@app.route("/products", methods=["POST"])
def create_product():
    new_product = {
        "id": len(products) + 1,
        "name": request.json["name"],
        "description": request.json["description"],
        "price": request.json["price"],
        "stock_level": request.json["stock_level"],
    }
    products.append(new_product)
    return jsonify(new_product), 201

# Endpoint to update an existing product
@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    product["name"] = request.json.get("name", product["name"])
    product["description"] = request.json.get("description", product["description"])
    product["price"] = request.json.get("price", product["price"])
    product["stock_level"] = request.json.get("stock_level", product["stock_level"])
    return jsonify(product)

# Endpoint to delete a product
@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = next((p for p in products if p["id"] == product_id), None)
    if product is None:
        return jsonify({"error": "Product not found"}), 404
    products.remove(product)
    return jsonify({"message": "Product deleted"})

# Endpoint to create a new order
@app.route("/orders", methods=["POST"])
def create_order():
    new_order = {
        "id": len(orders) + 1,
        "product_id": request.json["product_id"],
        "quantity": request.json["quantity"],
    }
    orders.append(new_order)
    # Update stock level
    product = next((p for p in products if p["id"] == new_order["product_id"]), None)
    if product is not None:
        product["stock_level"] -= new_order["quantity"]
    return jsonify(new_order), 201

# Endpoint to get all orders
@app.route("/orders", methods=["GET"])
def get_orders():
    return jsonify(orders)

if __name__ == "__main__":
    app.run(debug=True)