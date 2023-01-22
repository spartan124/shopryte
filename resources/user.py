from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256

from db import db
from model import UserModel
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token
from schemas import UserSchema

blp = Blueprint("Users", "users", description="Operations on users")

@blp.route("/register")
class RegisterUser(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        if UserModel.query.filter(UserModel.username == user_data["username"]).first():
            abort(409, message="User with this username already exist.")
        user = UserModel(
            username = user_data["username"],
            password = pbkdf2_sha256.hash(user_data["password"])
        )

        db.session.add(user)
        db.session.commit()
    
        return {"message": "User Created Successfully"}, 201
    
@blp.route("/login")
class Login(MethodView):
    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]
        ).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(identity=user.id)

            return {"access_token": access_token, "refresh_token": refresh_token}

        abort(401, message="Invalid credentials.")

@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)

        return {"access_token": new_token}

@blp.route("/user/<int:user_id>")
class User(MethodView):
    @jwt_required()
    @blp.response(200, UserSchema)
    def get(self, user_id):
        user = UserModel.query.get_or_404(user_id)
        return user
    
    @jwt_required()
    def delete(self, user_id):
        user = UserModel.query.get_or_404(user_id)

        db.session.delete(user)
        db.session.commit()
        
        return f"User with user ID {user_id} deleted", 200


@blp.route("/users")
class UserList(MethodView):
    @jwt_required()
    @blp.response(200, UserSchema(many=True))
    def get(self):
        all_users = UserModel.query.all()
        return all_users