import os
import flask.cli
import psycopg2
from flask import Flask , render_template , request , redirect , url_for , flash , session , jsonify

app = Flask(__name__)

app.secret_key = 'secret'


# Database connection function
def get_db_connection ():
    conn = psycopg2.connect(host="localhost" ,
                            database="market" ,
                            user="postgres" ,
                            password="qwer")
    return conn


# Login route
@app.route("/" , methods=['GET' , 'POST'])
def client_sign_in ():
    if request.method == 'POST':
        # Here you will handle the sign-in logic
        phone = request.form['phone']
        password = request.form['password']
        # Verify the phone and password with the database
        conn = get_db_connection()
        cur = conn.cursor()
        # This is a placeholder SQL query, you should adjust it as needed
        cur.execute('SELECT * FROM client WHERE phone_number = %s AND password = %s' , (str(phone) , password))
        client_data = cur.fetchone()
        cur.close()
        conn.close()
        if client_data:
            # Log in the client and redirect to a new page, e.g., the client's account page
            session['id_client'] = client_data[2]  # Assuming the client ID is the first field
            return redirect(url_for('client_account'))  # You need to create a 'client_account' route
        else:
            flash('Неверные данные для входа. Пожалуйста, попробуйте снова.' , 'login')
            return redirect(url_for('client_sign_in'))
    return render_template('clientSignIn.html')  # Render the sign-in page


@app.route('/adminSignIn' , methods=['GET' , 'POST'])
def adminSignIn ():
    # Render the sign-in page for GET requests
    if request.method == 'GET':
        return render_template('adminSignIn.html')

    # Process the form submission for POST requests
    fsc = request.form['fsc']
    password = request.form['password']
    conn = get_db_connection()
    cur = conn.cursor()

    # Execute a secure query using parameterized statements
    cur.execute('SELECT * FROM employee WHERE fsc = %s AND password = %s' , (fsc , password))
    employee_data = cur.fetchone()
    cur.close()
    conn.close()

    if employee_data:
        # Successful login
        session['id_employee'] = employee_data[0]  # Store employee ID in session
        return redirect(url_for('admin_account'))  # Redirect to the employee's account page
    else:
        # Failed login
        flash('Неверные данные для входа. Пожалуйста, попробуйте снова.' , 'error')
        return redirect(url_for('adminSignIn'))


@app.route("/admin")
def admin_account ():
    id = session['id_employee']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM employee WHERE id_employee = %s' , (str(id)))
    employee_data = cur.fetchone()
    cur.close()
    conn.close()
    return render_template("admin_home.html" , employee=employee_data)


@app.route("/client")
def client_account ():
    if 'id_client' not in session:
        return redirect(url_for('client_sign_in'))

    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch client details
    cur.execute('SELECT fcs, bonus_points FROM client WHERE id_client = %s' , (session['id_client'] ,))
    client_details = cur.fetchone()

    # Fetch products details
    cur.execute('SELECT id_product, cost, brand, specifications, availability FROM product_description')
    products = cur.fetchall()

    print(products)
    cur.close()
    conn.close()

    # Pass client and products data to the template
    print(client_details)
    return render_template('client.html' , client=client_details , products=products)


@app.route('/client/orders')
def showOrdersHistory ():
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch client details
    cur.execute('SELECT * FROM application WHERE id_client = %s' , (session['id_client'] ,))
    orders = cur.fetchall()
    conn.close()
    cur.close()
    print(orders)
    return render_template('orders_history.html' , orders=orders)


@app.route('/admin/products')
def showProducts ():
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch client details
    cur.execute('SELECT * FROM product_description ORDER BY id_product ASC ')
    products = cur.fetchall()
    conn.close()
    cur.close()
    print(products)
    return render_template('admin_products.html' , products=products)


@app.route('/add_product' , methods=['POST'])
def add_product ():
    try:
        # Convert form data to the correct types
        product_cost = int(request.form['product_cost'])
        product_brand = request.form['product_brand']
        product_specifications = request.form['product_specifications']

        # Check if 'product_availability' checkbox was checked
        product_availability = '1' if 'product_availability' in request.form and request.form[
            'product_availability'] == 'on' else '0'

        # Open a connection to the database
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("CALL add_new_product(%s,%s,%s,%s)" ,
                    (product_cost , product_brand , product_specifications , product_availability))

        # Commit the transaction
        conn.commit()

        # Close the cursor and the connection
        cur.close()
        conn.close()

        # Redirect to the products page or wherever is appropriate
        return redirect(url_for('showProducts'))
    except Exception as e:
        # Log the exception for debugging
        print("Error adding product:" , e)
        # Handle the error (e.g., flash a message to the user, log it, etc.)
        flash('Error adding product. Please check the data and try again.')

        # Redirect back to the add product page or show an error message
        return redirect(url_for('add_product'))


@app.route('/edit_product', methods=['POST'])
def edit_product():
    try:
        # Получите данные из формы
        product_id = request.form['product_id']
        print("Product ID:" , product_id)
        product_cost = int(request.form['product_cost'])
        product_brand = request.form['product_brand']
        product_specifications = request.form['product_specifications']
        product_availability = '1' if 'product_availability' in request.form else '0'

        # Open a connection to the database
        conn = get_db_connection()
        cur = conn.cursor()

        # Проверьте, существует ли продукт с таким ID
        cur.execute("SELECT * FROM product_description WHERE id_product = %s", (product_id,))
        product = cur.fetchone()

        if product:
            # Обновите данные продукта
            cur.execute("UPDATE product_description SET cost=%s, brand=%s, specifications=%s, availability=%s WHERE id_product=%s",
                        (product_cost, product_brand, product_specifications, product_availability, product_id))

            # Commit the transaction
            conn.commit()

            # Перенаправьте пользователя обратно на страницу со списком продуктов или на страницу продукта
            return redirect(url_for('showProducts'))
        else:
            # Продукт с таким ID не найден, верните сообщение об ошибке или перенаправьте на другую страницу
            return "Product not found", 404
    except Exception as e:
        # Log the exception for debugging
        print("Error editing product:", e)
        # Handle the error (e.g., flash a message to the user, log it, etc.)
        flash('Error editing product. Please check the data and try again.')
        # Redirect back to the edit product page or show an error message
        return redirect(url_for('edit_product'))
    finally:
        # Ensure that the cursor and connection are closed even if an error occurs
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/showOrders')
def showOrders():
    conn = get_db_connection()
    cur = conn.cursor()

    # Проверяем, существует ли продукт с указанным ID
    cur.execute("SELECT * FROM application ORDER BY id_application ASC")
    orders = cur.fetchall()
    cur.close()
    return render_template("admin_clients_orders.html", orders = orders)


@app.route('/order/<int:id>')
def showOrderInfo(id):
    conn = get_db_connection()
    cur = conn.cursor()

    # Проверяем, существует ли продукт с указанным ID
    cur.execute("SELECT * FROM application WHERE id_application = %s", (id,))
    order = cur.fetchone()
    cur.close()
    return render_template("admin_add_product.html" , application=order)


@app.route('/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        # Открываем соединение с базой данных (подставьте свой код для подключения к БД)
        conn = get_db_connection()
        cur = conn.cursor()

        # Проверяем, существует ли продукт с указанным ID
        cur.execute("SELECT * FROM product_description WHERE id_product = %s", (product_id,))
        product = cur.fetchone()

        if product:
            # Если продукт существует, удаляем его из базы данных
            cur.execute("DELETE FROM product_description WHERE id_product = %s", (product_id,))
            conn.commit()
            # Закрываем соединение с базой данных
            cur.close()
            conn.close()
            # Возвращаем успешный ответ
            return 'Product deleted successfully', 200
        else:
            # Если продукт с указанным ID не найден, возвращаем сообщение об ошибке
            return 'Product not found or deletion failed', 404
    except Exception as e:
        # Обрабатываем ошибку (например, логируем её и возвращаем сообщение об ошибке)
        print("Error deleting product:", e)
        return 'Error deleting product', 500

@app.route('/add-product')
def addProduct():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM product_description ORDER BY id_product ASC ')
    products = cur.fetchall()
    conn.close()
    cur.close()
    print(products)
    return render_template('add_in_application.html', products=products)



if __name__ == '__main__':
    app.run(debug=True)
