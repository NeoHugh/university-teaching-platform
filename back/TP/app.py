from flask import Flask, request, make_response, send_from_directory, url_for
from Classes import Base, Engine, select, PUser, Teacher, Student, Course, Manage, Homework, HandInHomework, Reference, \
    HandInHomework, session, TA, MyJSONEncoder, courseDescriptor2Name
import json
import os
from flask import render_template

app = Flask(__name__)
filePath = './static'


# app.debug = True


@app.route('/', methods=['GET'])
def welcome():
    return render_template('hehe.html')


# 登陆验证
@app.route('/loginValidness', methods=['GET'])
def loginValidness():
    userName = request.args.get('userName')
    passWD = request.args.get('passWD')
    type = request.args.get('type')
    stmt = f'select * from puser where userName = "{userName}" and passWD = "{passWD}"'
    resultSet = session.execute(stmt)
    match = 1 if resultSet.rowcount else 0
    identity = 0
    if (match == 1):
        if type == 'stu':
            stmt = f'select * from student where userName = "{userName}"'
            resultSet = session.execute(stmt)
            identity = 1 if resultSet.rowcount else 0
        elif type == 'ins':
            stmt = f'select * from teacher where userName = "{userName}"'
            resultSet = session.execute(stmt)
            identity = 1 if resultSet.rowcount else 0
        elif type == 'ta':
            stmt = f'select * from ta where userName = "{userName}"'
            resultSet = session.execute(stmt)
            identity = 1 if resultSet.rowcount else 0
        else:
            pass
    return json.dumps({'match': match, 'identity': identity}, indent=2, ensure_ascii=False)


'''
after login :
'''


# 获取某个用户信息
@app.route('/userInfo', methods=['GET'])
def userInfo():
    userName = request.args.get('userName')
    type = request.args.get('type')
    if type == 'stu':
        res = session.query(Student).filter(Student.userName == userName).all()
        stu = res[0]
        return json.dumps(stu, cls=MyJSONEncoder, indent=2, ensure_ascii=False)
    elif type == 'ins':
        res = session.query(Teacher).filter(Teacher.userName == userName).all()
        ins = res[0]
        return json.dumps(ins, cls=MyJSONEncoder, indent=2, ensure_ascii=False)
    elif type == 'ta':
        res = session.query(TA).filter(TA.userName == userName).all()
        ta = res[0]
        return json.dumps(ta, cls=MyJSONEncoder, indent=2, ensure_ascii=False)
    else:
        return json.dumps({'state': 404}, indent=2, ensure_ascii=False)


# 修改某个用户个人信息
@app.route('/modifyInfo', methods=['POST'])
def modifyInfo():
    userName = request.form['userName']
    nickName = request.form['nickName']
    passWD = request.form['passWD']
    try:
        stmt = f'update puser set puser.nickName = "{nickName}" where puser.userName = "{userName}"'
        # session.query(PUser).filter(PUser.userName == userName).update({'nickName':nickName})
        session.execute(stmt)
        session.commit()
        if passWD != '':
            stmt = f'update puser set puser.passWD = "{passWD}" where puser.userName = "{userName}"'
            session.execute(stmt)
            session.commit()
        return json.dumps({'state': 200}, indent=2, ensure_ascii=False)
    except:
        return json.dumps({'state': 404}, indent=2, ensure_ascii=False)


# 获取某人的待办列表
@app.route('/todolist', methods=['GET'])
def todolist():
    userName = request.args.get('userName')
    type = request.args.get('type')
    if type == 'stu':
        # 学生只回传作业列表
        stmt = f'select homeworkTitle,homework.startTime,homework.endTime,courseName from homework,participation,course where participation.studentUsername = "{userName}"'
        res = session.execute(stmt)
        todols = [{'作业名称': list(i)[0], '开始时间': list(i)[1], '结束时间': list(i)[2], '课程名称': list(i)[3]} for i in res]
        return json.dumps(todols, cls=MyJSONEncoder, indent=2, ensure_ascii=False)

    elif type == 'ta':
        stmt = f'SELECT submitUserName, handInTime, homeworkTitle,manage.courseDescriptor FROM handinhomework JOIN manage ON (handinhomework.courseDescriptor = manage.courseDescriptor)  WHERE manage.gradeHomework=1 and manage.userName = "{userName}"  and manage.courseDescriptor = (SELECT manage.courseDescriptor from manage NATURAL JOIN course WHERE manage.userName = "{userName}")'
        # similar to ins but ta requires gradeHomework privilege to be set to 1
        res = session.execute(stmt)
        todols = [{'提交者': list(i)[0], '提交时间': list(i)[1], '作业名称': list(i)[2], '课程名称': courseDescriptor2Name(list(i)[3])}
                  for i in res]
        return json.dumps(todols, cls=MyJSONEncoder, indent=2, ensure_ascii=False)

    elif type == 'ins':
        stmt = f'SELECT submitUserName, handInTime, homeworkTitle,manage.courseDescriptor FROM handinhomework JOIN manage ON (handinhomework.courseDescriptor = manage.courseDescriptor)  WHERE manage.userName = "{userName}"  and manage.courseDescriptor = (SELECT manage.courseDescriptor from manage NATURAL JOIN course WHERE manage.userName = "{userName}")'
        res = session.execute(stmt)
        todols = [{'提交者': list(i)[0], '提交时间': list(i)[1], '作业名称': list(i)[2], '课程名称': courseDescriptor2Name(list(i)[3])}
                  for i in res]
        return json.dumps(todols, cls=MyJSONEncoder, indent=2, ensure_ascii=False)
    else:
        return json.dumps({'state': 404}, indent=2, ensure_ascii=False)


# 老师/助教查看管理的课程
@app.route('/manageCourse', methods=['GET'])
def manageCourse():
    userName = request.args.get('userName')
    stmt = f'SELECT courseDescriptor,courseName FROM course NATURAL JOIN manage WHERE manage.userName = "{userName}"'
    res = session.execute(stmt)
    course_list = [
        {'课程标识符': i[0], '课程名称': i[1]} for i in
        res]
    return json.dumps(course_list, cls=MyJSONEncoder, indent=2, ensure_ascii=False)


# 学生查看学习的课程
@app.route('/studyCourse', methods=['GET'])
def studyCourse():
    userName = request.args.get('userName')
    stmt = f'SELECT courseDescriptor,courseName FROM course NATURAL JOIN participation WHERE participation.studentUserName = "{userName}"'
    res = session.execute(stmt)
    course_list = [
        {'课程标识符': i[0], '课程名称': i[1]} for i in
        res]
    return json.dumps(course_list, cls=MyJSONEncoder, indent=2, ensure_ascii=False)

# 获取文件的url
@app.route('/fetchFile', methods=['GET'])
def fetchFile():
    type = request.args.get('type')
    if type == '1':
        userName = request.args.get('userName')
        append = session.query(PUser.portrait).filter(PUser.userName == userName).all()[0][0]
        return json.dumps({'url': filePath + '/' + userName + '.' + append}, indent=2, ensure_ascii=False)
    elif type == '2':
        courseDescriptor = request.args.get('courseDescriptor')
        append = session.query(Course.Image).filter(Course.courseDescriptor == courseDescriptor).all()[0][0]
        return json.dumps({'url': filePath + '/' + courseDescriptor + '.' + append}, indent=2,
                          ensure_ascii=False)
    elif type == '3':
        file = request.args.get('file')
        append = session.query(HandInHomework.fileName).filter(HandInHomework.file == file).all()[0][0]
        return json.dumps({'url': filePath + r'/' + file + '.' + append.split('.')[1]}, indent=2, ensure_ascii=False)
    elif type == '4':
        file = request.args.get('file')
        append = session.query(Reference.referenceName).filter(Reference.file == file).all()[0][0]
        return json.dumps({'url': filePath + r'/' + file + '.' + append.split('.')[1]}, indent=2, ensure_ascii=False)
    else:
        # unexpected type
        pass
    return json.dumps({'state': 404})

# 获取某门课程的布置过的所有作业列表
@app.route('/homeworkList', methods=['GET'])
def homeworkList():
    courseDescriptor = request.args.get('courseDescriptor')
    res = session.query(Homework.homeworkTitle, Homework.homeworkContent, Homework.startTime, Homework.endTime).filter(
        Homework.courseDescriptor == courseDescriptor).all()
    res_list = [{'homeworkTitle': i[0], 'homeworkContent': i[1], 'startTime': i[2], 'endTime': i[3]} for i in res]
    return json.dumps(res_list, cls=MyJSONEncoder, indent=2, ensure_ascii=False)

# 获取某门课程某个作业的学生提交文件列表
@app.route('/handinList')
def handinList():
    courseDescriptor = request.args.get('courseDescriptor')
    hwName = request.args.get('homeworkName')
    res = session.query(HandInHomework.file, HandInHomework.fileName, HandInHomework.handInTime,
                        HandInHomework.submitUserName).filter(
        HandInHomework.courseDescriptor == courseDescriptor and HandInHomework.homeworkTitle == hwName).all()
    res_list = [{'file': i[0], 'fileName': i[1], 'handInTime': i[2], 'submitUserName': i[3]} for i in res]
    return json.dumps(res_list, cls=MyJSONEncoder, indent=2, ensure_ascii=False)

# 获取某课程课件列表
@app.route('/courseReference', methods=['GET'])
def courseReference():
    courseDescriptor = request.args.get('courseDescriptor')
    res = session.query(Reference.referenceName, Reference.downloadable, Reference.upLoadTime).filter(
        Reference.courseDescriptor == courseDescriptor).all()
    res_list = [{'referenceName': i[0], 'downloadable': i[1], 'upLoadTime': i[2]} for i in res]
    return json.dumps(res_list, cls=MyJSONEncoder, indent=2, ensure_ascii=False)

# 获取热门课程
@app.route('/hotCourse', methods=['GET'])
def hotCourse():
    page = int(request.args.get('page'))
    # 从0开始编号
    num = int(request.args.get('num'))
    stmt = 'SELECT distinct  course.courseDescriptor,course.credit, course.Image,course.courseName,course.semester,course.courseStart,course.courseEnd from course WHERE course.hotIndex > 4'
    res = session.execute(stmt)
    hotCourse = []
    for i, each in enumerate(res):
        if (page + 1) * num > i:
            hotCourse.append(
                {'courseDescriptor': each[0], 'credit': float(each[1]), 'Image': filePath + '/' + each[0] + '.' + each[2],
                 'courseName': each[3], 'semester': each[4], 'courseStart': each[5], 'courseEnd': each[6]})
        elif (page + 1) * num == i:
            return json.dumps(hotCourse, cls=MyJSONEncoder, indent=2, ensure_ascii=False)
    return json.dumps(hotCourse, cls=MyJSONEncoder, indent=2, ensure_ascii=False)



if __name__ == '__main__':
    app.run(debug=True)
