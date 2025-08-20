const Book = require('../models/Book');

// Get all books
exports.getAllBooks = async (req, res) => {
  try {
    const books = await Book.find().sort({ createdAt: -1 });
    res.render('index', { books, message: req.query.message });
  } catch (error) {
    console.error('Error fetching books:', error);
    res.status(500).render('error', { 
      message: 'Error fetching books', 
      error 
    });
  }
};

// Show add book form
exports.showAddForm = (req, res) => {
  res.render('add', { error: null, book: {} });
};

// Add new book
exports.addBook = async (req, res) => {
  try {
    const { title, author, year, isbn } = req.body;
    
    // Validation
    if (!title || !author || !year) {
      return res.render('add', { 
        error: 'Title, Author, and Year are required',
        book: req.body 
      });
    }

    const newBook = new Book({
      title: title.trim(),
      author: author.trim(),
      year: parseInt(year),
      isbn: isbn ? isbn.trim() : undefined
    });

    await newBook.save();
    res.redirect('/?message=Book added successfully');
  } catch (error) {
    console.error('Error adding book:', error);
    res.render('add', { 
      error: error.message || 'Error adding book',
      book: req.body 
    });
  }
};

// Show edit form
exports.showEditForm = async (req, res) => {
  try {
    const book = await Book.findById(req.params.id);
    if (!book) {
      return res.redirect('/?message=Book not found');
    }
    res.render('edit', { book, error: null });
  } catch (error) {
    console.error('Error fetching book:', error);
    res.redirect('/?message=Error fetching book');
  }
};

// Update book
exports.updateBook = async (req, res) => {
  try {
    const { title, author, year, isbn } = req.body;
    
    const updatedBook = await Book.findByIdAndUpdate(
      req.params.id,
      {
        title: title.trim(),
        author: author.trim(),
        year: parseInt(year),
        isbn: isbn ? isbn.trim() : undefined
      },
      { new: true, runValidators: true }
    );

    if (!updatedBook) {
      return res.redirect('/?message=Book not found');
    }

    res.redirect('/?message=Book updated successfully');
  } catch (error) {
    console.error('Error updating book:', error);
    const book = await Book.findById(req.params.id);
    res.render('edit', { 
      book: book || req.body, 
      error: error.message || 'Error updating book'
    });
  }
};

// Delete book
exports.deleteBook = async (req, res) => {
  try {
    const deletedBook = await Book.findByIdAndDelete(req.params.id);
    
    if (!deletedBook) {
      return res.redirect('/?message=Book not found');
    }

    res.redirect('/?message=Book deleted successfully');
  } catch (error) {
    console.error('Error deleting book:', error);
    res.redirect('/?message=Error deleting book');
  }
};

// Search books
exports.searchBooks = async (req, res) => {
  try {
    const { query } = req.query;
    
    if (!query) {
      return res.redirect('/');
    }

    const books = await Book.find({
      $or: [
        { title: { $regex: query, $options: 'i' } },
        { author: { $regex: query, $options: 'i' } },
        { isbn: { $regex: query, $options: 'i' } }
      ]
    }).sort({ createdAt: -1 });

    res.render('index', { books, message: `Search results for: ${query}` });
  } catch (error) {
    console.error('Error searching books:', error);
    res.status(500).render('error', { 
      message: 'Error searching books', 
      error 
    });
  }
};
