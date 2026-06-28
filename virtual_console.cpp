#include <iostream>

#include <string.h>

#include <math.h>

#include "python3.10/Python.h"

#define IS_WIN (defined(_WIN32) | defined(_WIN64))

#define IS_UNIX (defined(__linux__) | defined(__APPLE__) | defined(__unix__) | defined(__unix))

#if IS_WIN
#include <windows.h>
#include 
#else
#include <sys/ioctl.h>
#include <unistd.h>
#endif

using namespace std;

void set_cursor_pos(ssize_t col, ssize_t row) {
	cout << "\x1B[" << col << ";" << row << "H";
}

void get_terminal_size(ssize_t* columns, ssize_t* rows) {
	#if IS_WIN
	CONSOLE_SCREEN_BUFFER_INFO csbi;
    GetConsoleScreenBufferInfo(GetStdHandle(STD_OUTPUT_HANDLE), &csbi);
    if (columns) *columns = csbi.srWindow.Right - csbi.srWindow.Left + 1;
    if (rows) *rows = csbi.srWindow.Bottom - csbi.srWindow.Top + 1;
	#else
	winsize size;

	ioctl(STDOUT_FILENO, TIOCGWINSZ, &size);

	if (columns) *columns = size.ws_col;

	if (rows) *rows = size.ws_row;
	#endif
}

class VirtualConsole {
	private:
	string text_buf;

	char* view_buf; size_t view_buf_size;

	public:
	ssize_t column, row;
	
	ssize_t x, y, 
			columns, rows, 
			real_columns, real_rows;

	void operator delete(void* _ptr) {
		cout << "Cleaning... ";

		VirtualConsole* console = (VirtualConsole*)_ptr;

		console->close();

		cout << "done\n";
	}

	VirtualConsole& operator<<(const char* str) {
		this->write(str);

		return *this;
	}

	template<typename T>
	VirtualConsole& operator<<(T& obj) {
		string str = to_string(obj);

		this->write(str);

		return *this;
	}

	void open(ssize_t _columns=-1, ssize_t _rows=-1, ssize_t _x=-1, ssize_t _y=-1) {
		if (this->columns == _columns && this->rows == _rows) return;

		if (_columns != 0) this->columns = _columns;
		
		if (_rows != 0) this->rows = _rows;

		this->x = _x; this->y = _y;

		cout << "Opening VirtualConsole...";

		this->view_buf = NULL;

		this->update();

		cout << " done\n";
	}

	void write(const char* str, ssize_t bytes=-1) {
		if (bytes == -1) bytes = strlen(str);

		ssize_t size = this->real_columns * this->real_rows;

		ssize_t pos = (this->row * this->real_columns) + this->column;

		ssize_t end = pos + bytes;

		this->text_buf += str;

		this->column += bytes;
	}

	template<typename T>
	void write(const T& obj, ssize_t bytes=-1) {
		string str = to_string(obj);

		write(str, str.length());
	}

	void resize_view_buf(ssize_t columns, ssize_t rows) {
		this->view_buf_size = this->real_columns * this->real_rows * sizeof(char);
		
		this->view_buf = (char*)realloc(this->view_buf, this->view_buf_size);

		memset(this->view_buf, ' ', this->view_buf_size);

		this->view_buf[this->view_buf_size - 1] = '\0';
	}

	void update() {
		ssize_t term_columns, term_rows;

		get_terminal_size(&term_columns, &term_rows);

		if (this->columns < 0) this->real_columns = term_columns;

		else this->real_columns = this->columns;

		if (this->rows < 0) this->real_rows = term_rows;

		else this->real_rows = this->rows;
		
		this->resize_view_buf(this->real_columns, this->real_rows);

		for (int i = 0; i < text_buf.length(); i++) {
			int x = i % this->real_columns, y = i / this->real_columns;

			this->view_buf[i] = text_buf[i];
		}
	}

	void display() {
		this->update();

		set_cursor_pos(0, 0);

		cout << this->view_buf;
	}

	void close() {
		if (this->view_buf) {
			cout << "Cleaning VirtualConsole... ";
			
			free(this->view_buf);

			this->view_buf = NULL;

			cout << "done" << endl;
		}
	}
};

typedef struct VirtualConsoleObject {
	PyObject_HEAD
	VirtualConsole* console;
} VirtualConsoleObject;

PyObject* VirtualConsole_open(VirtualConsoleObject* self, PyObject* args) {
	ssize_t columns = 0, rows = 0, x = 0, y = 0;

	static char* keywords[] = { "columns", "rows", "x", "y", NULL };	
	
	if (PyTuple_Size(args) == 0) {
		columns = -1; rows = -1;
	}

	else if (!PyArg_ParseTuple(args, "|nnnn", &columns, &rows, &x, &y)) {
		PyErr_SetString(PyExc_ValueError, "Cannot parse the tuple of arguments or keywords");

		return NULL;
	}

	self->console->open(columns, rows, x, y);
	
	Py_RETURN_NONE;
}

PyObject* VirtualConsole_print(VirtualConsoleObject* self, PyObject* args) {
	self->console->write("Hello, world!");

	Py_RETURN_NONE;
}

PyObject* VirtualConsole_display(VirtualConsoleObject* self, PyObject* args) {
	self->console->display();

	Py_RETURN_NONE;
}

PyObject* VirtualConsole_close(VirtualConsoleObject* self, PyObject* args) {
	self->console->close();
	
	Py_RETURN_NONE;
}

void VirtualConsoleObject_dealloc(VirtualConsoleObject* self) {
	self->console->close();

	Py_TYPE(self)->tp_free((PyObject*)self);
}

int VirtualConsoleObject_init(VirtualConsoleObject* object) {
	object->console = new VirtualConsole();

	return 0;
}

int VirtualConsole_set_columns(VirtualConsoleObject* self, PyObject* value, void* closure) {
	if (!PyLong_Check(value)) {
		const char* expected_str = "Expected int, got";

		char* string = (char*)malloc(strlen(expected_str) + strlen(value->ob_type->tp_name) + 4);

		sprintf(string, "%s \"%s\"", expected_str, value->ob_type->tp_name);

		PyErr_SetString(PyExc_TypeError, string);

		free(string);

		return -1;
	}

	self->console->columns = PyLong_AsSsize_t(value);

	return 0;
}

int VirtualConsole_set_rows(VirtualConsoleObject* self, PyObject* value, void* closure) {
	if (!PyLong_Check(value)) {
		const char* expected_str = "Expected int, got";

		char* string = (char*)malloc(strlen(expected_str) + strlen(value->ob_type->tp_name) + 4);

		sprintf(string, "%s \"%s\"", expected_str, value->ob_type->tp_name);

		PyErr_SetString(PyExc_TypeError, string);

		free(string);

		return -1;
	}

	self->console->rows = PyLong_AsSsize_t(value);

	return 0;
}

int VirtualConsole_set_column(VirtualConsoleObject* self, PyObject* value, void* closure) {
	if (!PyLong_Check(value)) {
		const char* expected_str = "Expected int, got";

		char* string = (char*)malloc(strlen(expected_str) + strlen(value->ob_type->tp_name) + 4);

		sprintf(string, "%s \"%s\"", expected_str, value->ob_type->tp_name);

		PyErr_SetString(PyExc_TypeError, string);

		free(string);

		return -1;
	}

	self->console->column = PyLong_AsSsize_t(value);

	return 0;
}

int VirtualConsole_set_row(VirtualConsoleObject* self, PyObject* value, void* closure) {
	if (!PyLong_Check(value)) {
		const char* expected_str = "Expected int, got";

		char* string = (char*)malloc(strlen(expected_str) + strlen(value->ob_type->tp_name) + 4);

		sprintf(string, "%s \"%s\"", expected_str, value->ob_type->tp_name);

		PyErr_SetString(PyExc_TypeError, string);

		free(string);

		return -1;
	}

	self->console->row = PyLong_AsSsize_t(value);

	return 0;
}

PyObject* VirtualConsole_get_columns(VirtualConsoleObject* self, void* closure) {
	return PyLong_FromSsize_t(self->console->columns);
}

PyObject* VirtualConsole_get_rows(VirtualConsoleObject* self, void* closure) {
	return PyLong_FromSsize_t(self->console->rows);
}

PyObject* VirtualConsole_get_column(VirtualConsoleObject* self, void* closure) {
	return PyLong_FromSsize_t(self->console->column);
}

PyObject* VirtualConsole_get_row(VirtualConsoleObject* self, void* closure) {
	return PyLong_FromSsize_t(self->console->row);
}

PyMethodDef VirtualConsole_methods[] = {
	{"open", (PyCFunction)VirtualConsole_open, METH_VARARGS, "Opening/reopening the virtual console"},
	{"print", (PyCFunction)VirtualConsole_print, METH_VARARGS, "Printing data to the virtual console"},
	{"display", (PyCFunction)VirtualConsole_display, METH_VARARGS, "Displays the virtual console data to terminal"},
	{"close", (PyCFunction)VirtualConsole_close, METH_NOARGS, "Closing the virtual console"},
	{NULL}
};

PyGetSetDef VirtualConsole_members[] = {
	{"columns", (getter)VirtualConsole_get_columns, (setter)VirtualConsole_set_columns, "Get the VirtualConsole size in columns", NULL},
	{"rows", 	(getter)VirtualConsole_get_rows, 	(setter)VirtualConsole_set_rows, 	"Get the VirtualConsole size in rows", NULL},
	{"column", 	(getter)VirtualConsole_get_column, 	(setter)VirtualConsole_set_column, 	"Get the VirtualConsole cursor position in columns", NULL},
	{"row", 	(getter)VirtualConsole_get_row, 	(setter)VirtualConsole_set_row, 	"Get the VirtualConsole cursor position in rows", NULL},
	{NULL}
};

PyTypeObject VirtualConsoleType = {
	PyVarObject_HEAD_INIT(NULL, 0)
	.tp_name = "virtual_console.VirtualConsole",
	.tp_basicsize = sizeof(VirtualConsoleObject),
	.tp_itemsize = 0,
	.tp_dealloc = (destructor)VirtualConsoleObject_dealloc,
	.tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
	.tp_doc = "VirtualConsole class",
	.tp_methods = VirtualConsole_methods,
	.tp_getset = VirtualConsole_members,
	.tp_init = (initproc)VirtualConsoleObject_init,
	.tp_new = PyType_GenericNew,
};

PyObject* VirtualConsole_get_term_size(PyObject* args) {
	ssize_t columns = -1, rows = -1;

	get_terminal_size(&columns, &rows);

	PyObject* columns_object = PyLong_FromSsize_t(columns);

	if (!columns_object)
		return PyErr_NoMemory();

	PyObject* rows_object = PyLong_FromSsize_t(rows);

	if (!rows_object) {
		Py_DECREF(columns_object);

		return PyErr_NoMemory();
	}

	PyObject* result = PyTuple_New(2);

	if (!result) {
		Py_DECREF(columns_object);

		Py_DECREF(rows_object);

		return PyErr_NoMemory();
	}

	PyTuple_SET_ITEM(result, 0, columns_object);

	PyTuple_SET_ITEM(result, 1, rows_object);

	return result;
}

PyMethodDef methods[] = {
	{"get_term_size", (PyCFunction)VirtualConsole_get_term_size, METH_NOARGS, "Get the real terminal size"},
	{NULL}
};

PyModuleDef virtual_console_module = {
	PyModuleDef_HEAD_INIT,
	"virtual_console",
	"Virtual console beta",
	-1,
	methods
};

PyMODINIT_FUNC PyInit_virtual_console() {
	PyObject* m;

	if (PyType_Ready(&VirtualConsoleType) < 0) return NULL;

	m = PyModule_Create(&virtual_console_module);

	if (m == NULL) return NULL;

	Py_INCREF(&VirtualConsoleType);

	if (PyModule_AddObject(m, "VirtualConsole", (PyObject*)&VirtualConsoleType) < 0) {
		Py_DECREF(&VirtualConsoleType);

		Py_DECREF(m);

		return NULL;
	}

	return m;
}