import copy
from database import crud
import pydantic_models
import config
import fastapi
from fastapi import FastAPI, Query, Body
from pony.orm import select
from typing import Union


api = FastAPI()


@api.get('/user/{user_id}')
def read_user(user_id: str, query: str | None = None):
    if query:
        return {'item_id': user_id, 'query': query}
    return {'item_id': user_id}


@api.put('/user/{user_id}')
def update_user(user_id: int, user: pydantic_models.UserToUpdate = fastapi.Body()):
    return crud.update_user(user).to_dict()


@api.delete('/user/{user_id}')
@crud.db_session
def delete_user(user_id: int = fastapi.Path()):
    crud.get_user_by_id(user_id).delete()
    return True


@api.post('/user/create')
def create_user(user: pydantic_models.UserToCreate):
    return crud.create_user(tg_id=user.tg_ID, nick=user.nick if user.nick else None).to_dict()


@api.get('/get_info_by_user_id/{user_id:int}')
@crud.db_session
def get_info_about_user(user_id):
    return crud.get_user_info(crud.User[user_id])


@api.get('/get_user_balance_by_id/{user_id:int}')
@crud.db_session
def get_user_balance_by_id(user_id):
    crud.update_wallet_balance(crud.User[user_id].wallet)
    return crud.User[user_id].wallet.balance


@api.get('/get_total_balance')
@crud.db_session
def get_total_balance():
    balance = 0
    crud.update_all_wallets()
    for user in crud.User.select()[:]:
        balance += user.wallet.balance
    return balance


@api.get('/users')
@crud.db_session
def get_users():
    users = []
    for user in crud.User.select()[:]:
        users.append(user.to_dict())
    return users


@api.get('/user_by_tg_id/{tg_id:int}')
@crud.db_session
def get_user_by_tg_id(tg_id):
    user = crud.get_user_by_tg_id(tg_id)
    return crud.get_user_info(user)


@api.post('/create_transaction/{user_id}')
@crud.db_session
def create_transaction(user_id: int, receiver_address: str = fastapi.Body(), amount_btc_without_fee: Union[int, float] = fastapi.Body()):
    user = crud.User[user_id]
    transaction = crud.create_transaction(user, amount_btc_without_fee, receiver_address, testnet=True)
    crud.update_all_wallets()
    if isinstance(transaction, str):
        if transaction.startswith('Too'):
            return f'На вашем балансе не хватает средств с учетом комиссии: {amount_btc_without_fee}'
    else:
        return crud.get_transaction_info(transaction)


@api.get('/get_user_wallet/{user_id:int}')
@crud.db_session
def get_user_wallet(user_id):
    return crud.get_wallet_info(crud.User[user_id].wallet)


@api.get('/get_user_transactions/{user_id:int}')
@crud.db_session
def get_user_transactions(user_id):
    return crud.get_user_transactions(user_id)




# import fastapi
# import database
# import pydantic_models
# import config
# import copy
#
# from fastapi import Request
#
#
# api = fastapi.FastAPI()
#
# fake_database = {'users':[
#     {
#         "id":1,             # тут тип данных - число
#         "name":"Anna",      # тут строка
#         "nick":"Anny42",    # и тут
#         "balance": 15300    # а тут float
#      },
#
#     {
#         "id":2,             # у второго пользователя
#         "name":"Dima",      # такие же
#         "nick":"dimon2319", # типы
#         "balance": 160.23     # данных
#      }
#     ,{
#         "id":3,             # у третьего
#         "name":"Vladimir",  # юзера
#         "nick":"Vova777",   # мы специально сделаем
#         "balance": 200.1     # нестандартный тип данных в его балансе
#      }
# ],}
#
# response = {'Ответ': 'Который возвращает сервер'}
#
#
# @api.post('/user/create')
# def index(user: pydantic_models.User):
#     fake_database['users'].append(user.dict())
#     print(fake_database)
#     return {'User Created!': user}
#
# @api.get('/static/path')
# def hello():
#     return 'hello'
#
# @api.get('/about/us')
# def about():
#     return {'We are': 'Legion'}
#
# @api.get('/userid/{id:int}')
# def get_id(id):
#     return {'user': id}
#
# @api.get('/user_id/{id}')
# def get_id2(id: int):
#     return {'user': id}
#
# @api.get('/test/{id:int}/{text:str}/{custom_path:path}')
# def get_test(id, text, custom_path):
#     return {"id":id,
#             "":text,
#             "custom_path": custom_path}
#
# @api.get('/get_info_by_user_id/{id:int}')
# def get_info_about_user(id):
#     return fake_database['users'][id-1]
#
# @api.get('/get_user_balance_by_id/{id:int}')
# def get_user_balance(id):
#     return fake_database['users'][id-1]['balance']
#
# @api.get('/get_total_balance')
# def get_total_balance():
#     total_balance: float = 0
#     for user in fake_database['users']:
#         print(pydantic_models.User(**user))
#         total_balance += pydantic_models.User(**user).balance
#     return total_balance
#
# @api.get('/users/')
# def get_users(skip: int = 0, limit: int = 10):
#     print(fake_database['users'])
#     for user in fake_database['users']:
#         print(f'{type(user)}, {user}')
#     return fake_database['users'][skip: skip + limit]
#
# @api.get('/user/{user_id}')
# def read_user(user_id: str, query: str | None = None):
#     print(f'user_id: {user_id}, query: {query}')
#     if query:
#         return {'user_id': user_id, 'query': query}
#     return {'user_id': user_id}
#
# @api.put('/user/{user_id}')
# def update_user(user_id: int, user: pydantic_models.User = fastapi.Body()):
#     print(user_id)
#     print(user)
#     for index, u in enumerate(fake_database['users']):
#         print(f'{index}, {type(u)}, {u}')
#         if u['id'] == user_id:
#             fake_database['users'][index] = user.dict()
#             return user
#
# @api.delete('/user/{user_id}')
# def delete_user(user_id: int = fastapi.Path()):
#     for index, u in enumerate(fake_database['users']):
#         if u['id'] == user_id:
#             old_db = copy.deepcopy(fake_database)
#             del fake_database['users'][index]
#             return {'old_db': old_db, 'new_db': fake_database}

