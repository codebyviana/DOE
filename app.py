from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import os
import re
import mysql.connector

app = Flask(__name__)
app.secret_key = "doe_plus_secret"


db = None
cursor = None
db_error = None

try:
    db = mysql.connector.connect(
        host=os.getenv("MYSQLHOST", os.getenv("DB_HOST", "localhost")),
        user=os.getenv("MYSQLUSER", os.getenv("DB_USER", "root")),
        password=os.getenv("MYSQLPASSWORD", os.getenv("DB_PASSWORD", "#Jenifer2007")),
        database=os.getenv("MYSQLDATABASE", os.getenv("DB_NAME", "DOE")),
        port=int(os.getenv("MYSQLPORT", os.getenv("DB_PORT", "3306")))
    )

    cursor = db.cursor(dictionary=True)
    print("Conectado ao MySQL")

except mysql.connector.Error as err:
    db_error = err
    print("Erro conexão:", err)


def check_db():
    """Retorna (cursor, erro) para permitir páginas mostrarem falha de conexão."""
    return cursor, db_error


@app.route('/')
def tela1():
    cursor, err = check_db()
    if err:
        return render_template('error.html', message=f"Erro de conexão com o banco: {err}"), 500
    return render_template('tela1.html')


@app.route('/tela2')
def tela2():
    cursor, err = check_db()
    if err:
        return render_template('error.html', message=f"Erro de conexão com o banco: {err}"), 500
    return render_template('tela2.html')


@app.route('/tela2_1')
def tela2_1():
    cursor, err = check_db()
    if err:
        return render_template('error.html', message=f"Erro de conexão com o banco: {err}"), 500

    cursor.execute("SELECT id, nome FROM cidade ORDER BY nome")
    cidades = cursor.fetchall()
    return render_template('tela2_1.html', cidades=cidades)

@app.route('/buscar_homocentros/<int:cidade_id>')
def buscar_homocentros(cidade_id):
    cursor, err = check_db()
    if err:
        return jsonify({"error": str(err)}), 500

    cursor.execute("SELECT id, nome FROM homocentro WHERE cidade_id=%s ORDER BY nome", (cidade_id,))
    homocentros = cursor.fetchall()
    return jsonify(homocentros)

@app.route('/agendar', methods=['POST'])
def agendar():
    nome = request.form.get('nome')
    cpf = request.form.get('cpf')
    email = request.form.get('email')
    idade = request.form.get('idade')
    telefone = request.form.get('telefone')
    tipo_sanguineo = request.form.get('tipo_sanguineo')
    cep = request.form.get('cep')
    endereco = request.form.get('endereco')
    cidade_id = request.form.get('cidade')
    homocentro_id = request.form.get('homocentro')
    data_doacao = request.form.get('data_doacao')

    required_fields = {
        "Nome": nome,
        "CPF": cpf,
        "E-mail": email,
        "Idade": idade,
        "Telefone": telefone,
        "Tipo Sanguíneo": tipo_sanguineo,
        "CEP": cep,
        "Endereço": endereco,
        "Cidade": cidade_id,
        "Homocentro": homocentro_id,
        "Data da doação": data_doacao,
    }

    missing = [k for k, v in required_fields.items() if not v]
    if missing:
        flash(f"Preencha os campos obrigatórios: {', '.join(missing)}", "error")
        return redirect(url_for('tela2_1'))

    try:
        cursor.execute("""
            INSERT INTO usuario (nome,CPF,email,idade,telefone,tipo_sanguineo,cep,endereco,cidade_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (nome, cpf, email, idade, telefone, tipo_sanguineo, cep, endereco, cidade_id))
        db.commit()
        usuario_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO agendamento (usuario_id, homocentro_id, data_doacao)
            VALUES (%s,%s,%s)
        """, (usuario_id, homocentro_id, data_doacao))
        db.commit()

        flash("Agendamento realizado com sucesso!", "success")
    except mysql.connector.Error as err:
        db.rollback()
        flash(f"Erro ao salvar agendamento: {err}", "error")

    return redirect(url_for('tela2_1'))



@app.route('/tela2_2', methods=['GET', 'POST'])
def tela2_2():
    cursor, err = check_db()
    if err:
        return render_template('error.html', message=f"Erro de conexão com o banco: {err}"), 500

    cpf = request.values.get('cpf', '').strip()
    agendamentos = []

    if cpf:
        cursor.execute("""
            SELECT a.id, u.nome AS usuario, u.cpf AS usuario_cpf, h.nome AS homocentro, c.nome AS cidade, a.data_doacao, a.status
            FROM agendamento a
            JOIN usuario u ON a.usuario_id = u.id
            JOIN homocentro h ON a.homocentro_id = h.id
            JOIN cidade c ON h.cidade_id = c.id
            WHERE u.cpf = %s
            ORDER BY a.data_doacao
        """, (cpf,))
        agendamentos = cursor.fetchall()

    return render_template('tela2_2.html', agendamentos=agendamentos, cpf=cpf)


@app.route('/tela2_3')
def tela2_3():
    cursor, err = check_db()
    if err:
        return render_template('error.html', message=f"Erro de conexão com o banco: {err}"), 500
    return render_template('tela2_3.html')

@app.route('/tela2_4/<int:id>', methods=['GET', 'POST'])
def tela2_4(id):
    cursor, err = check_db()
    if err:
        return render_template('error.html', message=f"Erro de conexão com o banco: {err}"), 500

    cpf_provided = request.values.get('cpf', '').strip()

    cursor.execute("""
        SELECT a.id, a.data_doacao, a.homocentro_id, u.nome AS usuario_nome, u.cpf AS usuario_cpf, h.cidade_id
        FROM agendamento a
        JOIN usuario u ON a.usuario_id = u.id
        JOIN homocentro h ON a.homocentro_id = h.id
        WHERE a.id=%s
    """, (id,))
    agendamento = cursor.fetchone()

    if not agendamento:
        flash("Agendamento não encontrado.", "error")
        return redirect(url_for('tela2_2'))


    cpf_digits = re.sub(r"\D", "", cpf_provided)
    stored_cpf = re.sub(r"\D", "", (agendamento.get('usuario_cpf') or ''))
    cpf_ok = bool(cpf_digits and cpf_digits == stored_cpf)

    if request.method == 'POST':
        action = request.form.get('action')

        if not cpf_ok:
            flash("CPF incorreto. Não é possível editar/excluir.", "error")
            return redirect(url_for('tela2_4', id=id))

        if action == 'delete':
            cursor.execute("DELETE FROM agendamento WHERE id=%s", (id,))
            db.commit()
            flash("Agendamento excluído com sucesso.", "success")
            return redirect(url_for('tela2_2'))

        homocentro_id = request.form.get('homocentro')
        data_doacao = request.form.get('data_doacao')
        cursor.execute(
            "UPDATE agendamento SET homocentro_id=%s, data_doacao=%s WHERE id=%s",
            (homocentro_id, data_doacao, id)
        )
        db.commit()
        flash("Agendamento atualizado com sucesso!", "success")
        return redirect(url_for('tela2_2'))

    cursor.execute("SELECT id, nome FROM cidade ORDER BY nome")
    cidades = cursor.fetchall()

    return render_template(
        'tela2_4.html',
        agendamento=agendamento,
        cidades=cidades,
        cpf_provided=cpf_provided,
        cpf_ok=cpf_ok
    )


@app.route('/tela2_5')
def tela2_5():
    cursor, err = check_db()
    if err:
        return render_template('error.html', message=f"Erro de conexão com o banco: {err}"), 500
    return render_template('tela2_5.html')


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)