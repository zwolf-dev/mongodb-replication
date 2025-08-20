const express = require('express');
const router = express.Router();
const bookController = require('../controllers/bookController');

// Home page - list all books
router.get('/', bookController.getAllBooks);

// Search books
router.get('/search', bookController.searchBooks);

// Show add book form
router.get('/add', bookController.showAddForm);

// Add new book
router.post('/add', bookController.addBook);

// Show edit form
router.get('/edit/:id', bookController.showEditForm);

// Update book
router.post('/edit/:id', bookController.updateBook);

// Delete book
router.post('/delete/:id', bookController.deleteBook);

module.exports = router;
