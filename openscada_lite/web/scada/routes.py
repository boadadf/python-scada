from flask import jsonify, request, render_template
from . import scada_bp

@scada_bp.route("/")
def scada_index():
    return render_template("scada.html")

@scada_bp.route("/login")
def scada_login():
    return render_template("scada.html")