from flask import request, redirect, url_for, flash, render_template, jsonify
from database.models.client import Client
from database.db import db
from services.audit_service import AuditService
from utils.validators import validate_client
import pytz
from datetime import datetime

BOGOTA = pytz.timezone('America/Bogota')

class ClientsController:
    @staticmethod
    def index():
        search = request.args.get('q', '')
        query = Client.query.filter(Client.is_active == True)
        if search:
            query = query.filter(Client.full_name.ilike(f'%{search}%'))
        clients = query.order_by(Client.full_name).all()
        return render_template('clients/clients.html', clients=clients, search=search)

    @staticmethod
    def create():
        if request.method == 'POST':
            errors = validate_client(request.form)
            if errors:
                for e in errors:
                    flash(e, 'danger')
                return render_template('clients/create_client.html', data=request.form)
            client = Client(
                full_name=request.form['full_name'],
                document_type=request.form['document_type'],
                document_number=request.form['document_number'],
                email=request.form.get('email'),
                phone=request.form.get('phone'),
                emergency_contact=request.form.get('emergency_contact'),
                emergency_phone=request.form.get('emergency_phone'),
                notes=request.form.get('notes')
            )
            db.session.add(client)
            db.session.commit()
            AuditService.log('create', 'clients', client.id, None, client.full_name)
            flash('Cliente registrado exitosamente.', 'success')
            return redirect(url_for('clients.index'))
        return render_template('clients/create_client.html')

    @staticmethod
    def edit(client_id):
        client = Client.query.get_or_404(client_id)
        if request.method == 'POST':
            old = client.full_name
            client.full_name = request.form['full_name']
            client.phone = request.form.get('phone')
            client.email = request.form.get('email')
            db.session.commit()
            AuditService.log('update', 'clients', client.id, old, client.full_name)
            flash('Cliente actualizado.', 'success')
            return redirect(url_for('clients.index'))
        return render_template('clients/edit_client.html', client=client)

    @staticmethod
    def deactivate(client_id):
        client = Client.query.get_or_404(client_id)
        client.is_active = False
        db.session.commit()
        AuditService.log('delete', 'clients', client.id, 'activo', 'inactivo')
        flash('Cliente desactivado.', 'warning')
        return redirect(url_for('clients.index'))

    @staticmethod
    def detail(client_id):
        client = Client.query.get_or_404(client_id)
        return render_template('clients/client_details.html', client=client)
