import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start =  (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)
  #Set up CORS. Allow '*' for origins.
  CORS(app, resources={'/': {'origins': '*'}})

  #Use the after_request decorator to set Access-Control-Allow
  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
    return response

  #Handle GET requests for all available categories.
  @app.route('/categories')
  def get_categories():
    categories = Category.query.all()
    categories_dict = {}
    for category in categories:
      categories_dict[category.id] = category.type
    
    # abort 404 if no categories found
    if (len(categories_dict) == 0):
      abort(404)
    
    # return data to view
    return jsonify({
      'success': True,
      'categories': categories_dict
      })

  #Handle GET requests for questions, including pagination (every 10 questions). 
  @app.route('/questions', methods=['GET'])
  def get_questions():
    selection = Question.query.all()
    total_questions = len(selection)
    current_questions = paginate_questions(request, selection)

    categories = Category.query.all()
    categories_dict = {}
    for category in categories:
        categories_dict[category.id] = category.type

    # abort 404 if no questions
    if (len(current_questions) == 0):        
        abort(404)

    # return data to view
    return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': total_questions,
        'categories': categories_dict
    })

  #Handle DELETE question using a question ID. 
  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question is None:
        abort(404)

      question.delete()
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'deleted': question_id,
        'questions': current_questions,
        'total_questions': len(Question.query.all())
      })

    except:
      abort(422)

  #Handle POST a new question, which will require the question and answer text, category, and difficulty score.
  @app.route('/questions', methods=['POST'])
  def create_question():
    body = request.get_json()
            
    new_question = body.get('question')
    new_answer = body.get('answer')
    new_difficulty = body.get('difficulty')
    new_category = body.get('category')

    try:
      question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
      question.insert()

      if ((new_question is None) or (new_answer is None) or (new_difficulty is None) or (new_category is None)):
        abort(422)

      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'created': question.id,
        'questions': current_questions,
        'total_questions': len(Question.query.all())
      })
    except:
      abort(422)

  #Get questions based on a search term. 
  @app.route('/questions/search', methods=['POST'])
  def search_questions():
    body = request.get_json()
    search_term = body.get('searchTerm',None)
    if search_term :
      selection = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'questions': current_questions,
        'total_questions': len(selection)
      })
    abort(404)
  
  #get questions based on category.
  @app.route('/categories/<int:id>/questions')
  def get_questions_by_category(id):
    category = Category.query.filter_by(id=id).one_or_none()

    if (category is None):
        abort(400)

    selection = Question.query.filter_by(category=category.id).all()
    questions_by_category = paginate_questions(request, selection)

    return jsonify({
        'success': True,
        'questions': questions_by_category,
        'total_questions': len(selection),
        'current_category': category.type
    })

  #get questions to play the quiz. 
  @app.route('/quizzes', methods=['POST'])
  def play_quiz():
    body = request.get_json()
    previous_questions = body.get('previous_questions')
    category = body.get('quiz_category')

    if ((category is None) or (previous_questions is None)):
        abort(400)

    if (category['id'] == 0):
        questions = Question.query.all()
    else:
        questions = Question.query.filter_by(category=category['id']).all()
    
    total = len(questions)

    random_question = []
    used = False
    
    for question in questions:
      random_question = questions[random.randrange(0, len(questions), 1)]
      if random_question.id not in previous_questions:
        used = True
        break
      if not used:
        pass
    if (len(previous_questions) == total):
      return jsonify({
          'success': True
      })

    return jsonify({
      'success': True,
      'question': random_question.format()
      })
                
  #error handlers for all expected errors 
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success": False, 
      "error": 404,
      "message": "resource not found"
      }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False, 
      "error": 422,
      "message": "unprocessable"
      }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False, 
      "error": 400,
      "message": "bad request"
      }), 400

  @app.errorhandler(405)
  def method_not_allowed(error):
    return jsonify({
      "success": False, 
      "error": 405,
      "message": "method not allowed"
      }), 405
  
  return app