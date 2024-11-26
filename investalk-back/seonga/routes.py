from flask import Blueprint, jsonify, request
from .models import Users, FavoriteStocks, db
from utils import token_required  # token_required 가져오기
from .utils import get_stock_data
from .dtos import UserDTO, FavoriteStockDTO

# 블루프린트 생성
main_bp = Blueprint('main', __name__)


# 메인 화면
@main_bp.route('/')
def index():
    return jsonify({"message": "Welcome to the InvesTalk API!"})

# 전체 사용자 목록 조회
@main_bp.route('/api/users', methods=['GET'])
@token_required
def get_users(current_user):
    users = Users.query.all()
    user_dtos = [UserDTO(user.id, user.name, user.email) for user in users]
    return jsonify([user.to_dict() for user in user_dtos])

# 사용자 생성
@main_bp.route('/api/users', methods=['POST'])
def create_user():
    name = request.json.get('name')
    email = request.json.get('email')

    existing_user = Users.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "사용자가 이미 존재합니다."}), 400

    new_user = Users(name=name, email=email)
    db.session.add(new_user)
    db.session.commit()

    user_dto = UserDTO(new_user.id, new_user.name, new_user.email)
    return jsonify(user_dto.to_dict()), 201

# 사용자 조회
@main_bp.route('/api/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    user = Users.query.get(user_id)
    if not user:
        return jsonify({"error": "사용자를 찾을 수 없습니다."}), 404

    user_dto = UserDTO(user.id, user.name, user.email)
    return jsonify(user_dto.to_dict())

# 사용자 수정
@main_bp.route('/api/users/<int:user_id>', methods=['PUT'])
@token_required
def update_user(current_user, user_id):
    user = Users.query.get(user_id)
    if not user:
        return jsonify({"error": "사용자를 찾을 수 없습니다."}), 404

    name = request.json.get('name', user.name)
    email = request.json.get('email', user.email)

    user.name = name
    user.email = email
    db.session.commit()

    user_dto = UserDTO(user.id, user.name, user.email)
    return jsonify(user_dto.to_dict())

# 사용자 삭제
@main_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(current_user, user_id):
    user = Users.query.get(user_id)
    if not user:
        return jsonify({"error": "사용자를 찾을 수 없습니다."}), 404

    FavoriteStocks.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "사용자가 삭제되었습니다."})

# 로그인된 사용자 정보(ID) 조회
@main_bp.route('/api/user_info', methods=['GET'])
@token_required
def get_user_info(current_user):
    return jsonify({
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"]
    })

# 사용자 관심 종목 목록 및 데이터 조회
@main_bp.route('/api/user/favorite_stocks', methods=['GET'])
@token_required
def get_favorite_stocks_with_data(current_user):
    try:
        # 디버깅용 출력
        print(f"Fetching favorite stocks for user: {current_user}")

        favorite_stocks = FavoriteStocks.query.filter_by(user_id=current_user['id']).all()
        if not favorite_stocks:
            return jsonify([])  # 빈 배열 반환

        stocks_data = []
        for favorite in favorite_stocks:
            symbol = favorite.symbol
            stock_info = get_stock_data(symbol)

            # 'Earnings Date' 키를 안전하게 처리
            earnings_date = stock_info.get('Earnings Date', 'N/A')
            stock_info["실적발표날짜"] = earnings_date

            stock_info["나의희망가격"] = favorite.desired_price
            stocks_data.append(stock_info)

        return jsonify(stocks_data)
    except Exception as e:
        print(f"Error in get_favorite_stocks_with_data: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


# 사용자 관심 종목 추가
@main_bp.route('/api/user/add_favorite', methods=['POST'])
@token_required
def add_favorite_stock(current_user):
    try:
        symbol = request.json.get('symbol')
        desired_price = request.json.get('desired_price')

        if not symbol:
            return jsonify({"error": "symbol 값이 필요합니다."}), 400

        # 이미 관심 종목인지 확인
        existing_favorite = FavoriteStocks.query.filter_by(user_id=current_user['id'], symbol=symbol).first()
        if existing_favorite:
            return jsonify({"error": f"{symbol} 종목은 이미 관심 목록에 있습니다."}), 400

        new_favorite = FavoriteStocks(user_id=current_user['id'], symbol=symbol, desired_price=desired_price)
        db.session.add(new_favorite)
        db.session.commit()

        return jsonify({
            "id": current_user["id"],
            "symbol": symbol,
            "desired_price": desired_price
        }), 201
    except Exception as e:
        print(f"Error in add_favorite_stock: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# 사용자 희망 가격 업데이트
@main_bp.route('/api/user/update_price', methods=['POST'])
@token_required
def update_desired_price(current_user):
    try:
        symbol = request.json.get('symbol')
        desired_price = request.json.get('desired_price')

        favorite_stock = FavoriteStocks.query.filter_by(user_id=current_user['id'], symbol=symbol).first()
        if not favorite_stock:
            return jsonify({"error": "종목을 찾을 수 없습니다."}), 404

        favorite_stock.desired_price = desired_price
        db.session.commit()

        return jsonify({"message": f"{symbol}의 희망 가격이 {desired_price}로 수정되었습니다."}), 200
    except Exception as e:
        print(f"Error in update_desired_price: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# 관심 종목 삭제
@main_bp.route('/api/user/remove_favorite', methods=['DELETE'])
@token_required
def remove_favorite_stock(current_user):
    try:
        symbol = request.json.get('symbol')

        favorite_stock = FavoriteStocks.query.filter_by(user_id=current_user['id'], symbol=symbol).first()
        if not favorite_stock:
            return jsonify({"error": "종목을 찾을 수 없습니다."}), 404

        db.session.delete(favorite_stock)
        db.session.commit()

        return jsonify({"message": f"{symbol}가 관심 종목에서 삭제되었습니다."})
    except Exception as e:
        print(f"Error in remove_favorite_stock: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
