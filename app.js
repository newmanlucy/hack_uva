require('dotenv').config();
const express = require('express');
// const ejs = require('ejs');
const pug = require('pug');
const bodyParser = require('body-parser');
const sqlite3 = require('sqlite3').verbose();
const FB = require('fb');
const async = require('async');
const lessMiddleware = require('less-middleware');

const app = express();

app.use(bodyParser.urlencoded({
    extended: true
}));

app.configure(function() {
    app.use(lessMiddleware({
        src: __dirname + "/static",
        compress: "/true"
    }));
    app.use(express.static("/static"));
});

app.use(express.static(__dirname + "/static"));

app.set('view engine', 'pug');

// app.get('/login', (req, res) => res.render('login'));

// app.get('/profile', (req, res) => res.render('profile'));

var get_instr_name = function (req, res, next) {
    console.log("here");
    let db = new sqlite3.Database('./scraper/uchi_evaluations.db', (err) => {
    if (err) {
        console.error(err.message);
    }
        console.log('Connected to the database.');
    });
    instructor_id = req.params['instructor_id'];
    name_sql = `SELECT (instructor_name) FROM instructors WHERE instructor_id = ?;`
    eval_sql = `SELECT * \
        FROM instructor_evals \
        WHERE instructor_id = ?;`
    db.serialize(() => {
        db.get(name_sql, [instructor_id], (err, row) => {
            req.instructor_name = row['instructor_name'];
            console.log(req.instructor_name);
        });
        db.get(eval_sql, [instructor_id], (err, row) => {
            console.log(row);
        });
    });

    db.close();
   
    next()
}

// app.use('/eval/:instructor_id', get_instr_name);

app.get('/eval/:instructor_id', (req, res) => {
    console.log("here");
    let db = new sqlite3.Database('./scraper/uchi_evaluations.db', (err) => {
    if (err) {
        console.error(err.message);
    }
        console.log('Connected to the database.');
    });
    instructor_id = req.params['instructor_id']
    var instructor_name;
    var eval = {
            "classes_taught": ["class name 1", "class name 2"],
            "organized": ["organized"],
            "pos_attitude": ["positive attitude"],
            "recommend": ["recommend"]
    };
    name_sql = `SELECT (instructor_name) FROM instructors WHERE instructor_id = ?;`
    eval_sql = `SELECT * \
        FROM instructor_evals \
        WHERE instructor_id = ?;`
    db.serialize(() => {
        db.get(name_sql, [instructor_id], (err, row) => {
            instructor_name = row['instructor_name'];
            console.log(instructor_name);
        });
        db.get(eval_sql, [instructor_id], (err, row) => {
            console.log(row);
        });
        res.render('eval', { 
            instructor_name: instructor_name,
            eval: eval
        });
    });

    db.close();
    console.log("final step");
    console.log(res.instructor_name);
    var instructor_name;
    var eval = {
            "classes_taught": ["class name 1", "class name 2"],
            "organized": ["organized"],
            "pos_attitude": ["positive attitude"],
            "recommend": ["recommend"]
        }


});

app.listen(3000, () => console.log('Server Started'));