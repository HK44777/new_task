from flask import Flask, render_template,flash,url_for,redirect,request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField,DateField,TimeField,IntegerRangeField,SelectField,TextAreaField
from wtforms.validators import DataRequired,Email,Length,EqualTo
import os
import pandas as pd
from flask_mail import Mail, Message

name=""
email=""
main_list=[]
tasks_dic={}
global count
count=0

app = Flask(__name__)
app.config['SECRET_KEY'] = "123456789"

app.config['MAIL_SERVER'] = 'smtp.gmail.com' 
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'hemanthkumar.r2005@gmail.com' 
app.config['MAIL_PASSWORD'] = 'jcqnpzopxrlculjl'  
app.config['MAIL_DEFAULT_SENDER'] = 'hemanthkumar.r2005@gmail.com'

mail = Mail(app)

ta= {
    'Work': [
        ('Finish report', '2024-12-01','10:00 AM', '10'),
        ('Email client', '2024-12-02','7:00 PM', '7'),
    ],
    'Personal': [
        ('Buy groceries', '2024-12-03', '10:00 AM', '10'),
        ('Workout', '2024-12-04', '10:00 AM', '10'),
    ],
}

class SignUpForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(),Email()])
    password = PasswordField("Password", validators=[DataRequired(),Length(min=8)])
    confirm_password=PasswordField("Confirm Password", validators=[DataRequired(),EqualTo('password', message="Passwords must match.")])
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(),Email()])
    password = PasswordField("Password", validators=[DataRequired(),Length(min=8)])
    submit = SubmitField("Login")

class TaskForm(FlaskForm):
    name = StringField("Task Name", validators=[DataRequired(), Length(min=1, max=250)])
    list_name = SelectField(
        "Select List",
        choices=main_list,
        validators=[DataRequired()]
    ) 
    deadline_date = DateField("Deadline Date", validators=[DataRequired()], format='%Y-%m-%d')
    deadline_time = TimeField("Deadline Time", validators=[DataRequired()])
    priority = IntegerRangeField("Priority (1 to 10)", default=5) 
    submit = SubmitField("Add Task")

class EditForm(FlaskForm):
    name = StringField("Task Name", validators=[DataRequired(), Length(min=1, max=250)])
    list_name = SelectField(
        "Select List",
        choices=main_list,
        validators=[DataRequired()]
    ) 
    deadline_date = DateField("Deadline Date", validators=[DataRequired()], format='%Y-%m-%d')
    deadline_time = TimeField("Deadline Time", validators=[DataRequired()])
    priority = IntegerRangeField("Priority (1 to 10)", default=5)
    submit = SubmitField("Save Changes")

class ContactForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(message="Name is required")])
    email = StringField('Email', validators=[DataRequired(message="Email is required"), Email(message="Invalid email address")])
    message = TextAreaField('Query', validators=[DataRequired(message="Query cannot be empty")])
    submit = SubmitField('Send')

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    global name,email
    signform = SignUpForm()
    if signform.validate_on_submit():
        name = signform.name.data
        email= signform.email.data
        return redirect(url_for('tasks'))
    return render_template('sign_up.html', form=signform)


@app.route("/login",methods=["GET","POST"])
def login():
    login_form=LoginForm()
    if login_form.validate_on_submit():
        return redirect(url_for('tasks'))
    return render_template("login.html",form=login_form)

@app.route("/tasks")
def tasks():
    return render_template("task_list.html", lists=main_list,tas=tasks_dic)

@app.route('/create-list', methods=['POST'])
def create_list():
    list_name = request.form.get('list_name') 
    if list_name: 
        main_list.append(list_name)  
    return redirect(url_for('tasks')) 

@app.route('/add_tasks',methods=['POST','GET'])
def add_tasks():
    form = TaskForm()
    global count
    if form.validate_on_submit():
        count+=1
        task_name = form.name.data
        list_name = form.list_name.data
        deadline_date = form.deadline_date.data
        deadline_time = form.deadline_time.data
        priority = form.priority.data
        if list_name in tasks_dic:
            tasks_dic[list_name].append([task_name,deadline_date,deadline_time,priority,count])
        else:
            tasks_dic[list_name]=[[task_name,deadline_date,deadline_time,priority,count]]
        return redirect(url_for('tasks'))
    return render_template('add_tasks.html', form=form)

@app.route('/edit_tasks/<string:l>/<int:c>', methods=['POST', 'GET'])
def edit_tasks(l, c):
    task_to_edit = None
    editform = EditForm()
    for i in tasks_dic[l]:
        if c == i[4]: 
            task_to_edit = i
            break 
    if editform.validate_on_submit():
        tasks_dic[l].remove(task_to_edit)
        task_to_edit[0] = editform.name.data
        task_to_edit[1] = editform.deadline_date.data
        task_to_edit[2] = editform.deadline_time.data
        task_to_edit[3] = editform.priority.data

        new_list_name = editform.list_name.data
        if new_list_name not in tasks_dic:
            tasks_dic[new_list_name] = []
        tasks_dic[new_list_name].append(task_to_edit)

        return redirect(url_for('tasks'))

    return render_template('edit_tasks.html', form=editform, lists=main_list, l=l, tas=task_to_edit)

@app.route('/move_task', methods=['POST'])
def move_task():
    target_list = request.form.get('target_list')
    return redirect(url_for('tasks'))

@app.route('/profile',methods=['GET'])
def profile():
    return render_template("profile.html",name=name)

@app.route('/send_csv', methods=['POST','GET'])
def send_csv():
    list_name="Work"
    task_data = ta[list_name]
    df = pd.DataFrame(task_data, columns=['Task', 'Deadline date','Deadline time', 'Priority'])
    csv_filename = f"{list_name}_tasks.csv"
    csv_filepath = os.path.join('tmp', csv_filename) 
    os.makedirs('tmp', exist_ok=True)
    df.to_csv(csv_filepath, index=False)

    msg = Message(f"Task List: {list_name}", recipients=[email])
    msg.body = f"Please find attached the CSV file for the '{list_name}' task list."
    with open(csv_filepath, 'rb') as f:
        msg.attach(csv_filename, 'text/csv', f.read())
    mail.send(msg)
    if os.path.exists(csv_filepath):
        os.remove(csv_filepath)

    return redirect(url_for('tasks'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    cform = ContactForm()
    if cform.validate_on_submit():
        name = cform.name.data
        email = cform.email.data
        message = cform.message.data
        return redirect(url_for('tasks'))

    return render_template('contact.html', form=cform)

@app.route("/delete", methods=["POST"])
def delete_item():
    return redirect(url_for("tasks"))

if __name__ == '__main__':
    app.run(debug=True)