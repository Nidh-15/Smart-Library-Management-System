
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import date

# ==========================================
# 1. DATABASE SETUP
# ==========================================

conn = sqlite3.connect("library.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    category TEXT,
    isbn TEXT UNIQUE,
    quantity INTEGER DEFAULT 1
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS borrowings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    member_id INTEGER,
    borrow_date TEXT,
    return_date TEXT,
    status TEXT DEFAULT 'Borrowed',
    FOREIGN KEY(book_id) REFERENCES books(id),
    FOREIGN KEY(member_id) REFERENCES members(id)
)
""")

conn.commit()

# Add sample data on first launch
cursor.execute("SELECT COUNT(*) FROM books")
if cursor.fetchone()[0] == 0:
    sample_books = [
        ("Python Programming", "John Zelle", "Programming", "ISBN001", 5),
        ("Atomic Habits", "James Clear", "Self Help", "ISBN002", 4),
        ("Rich Dad Poor Dad", "Robert Kiyosaki", "Finance", "ISBN003", 3),
        ("The Alchemist", "Paulo Coelho", "Fiction", "ISBN004", 5),
        ("Deep Work", "Cal Newport", "Productivity", "ISBN005", 3),
        ("Introduction to AI", "Philip C. Jackson", "Technology", "ISBN006", 2)
    ]
    cursor.executemany("""
        INSERT INTO books (title, author, category, isbn, quantity)
        VALUES (?, ?, ?, ?, ?)
    """, sample_books)

cursor.execute("SELECT COUNT(*) FROM members")
if cursor.fetchone()[0] == 0:
    sample_members = [
        ("Rahul Sharma", "rahul@gmail.com", "9876543210"),
        ("Priya Singh", "priya@gmail.com", "9876543211"),
        ("Aman Verma", "aman@gmail.com", "9876543212")
    ]
    cursor.executemany("""
        INSERT INTO members (name, email, phone)
        VALUES (?, ?, ?)
    """, sample_members)

conn.commit()


# ==========================================
# 2. MAIN APPLICATION
# ==========================================

root = tk.Tk()
root.title("Smart Library Management System")
root.geometry("1100x720")
root.minsize(900, 600)
root.configure(bg="#111827")

BG = "#111827"
PANEL = "#1F2937"
PURPLE = "#7C6CF0"
WHITE = "#F9FAFB"
MUTED = "#9CA3AF"
GREEN = "#22C55E"


# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================

def create_table(parent, columns):
    table = ttk.Treeview(
        parent,
        columns=columns,
        show="headings",
        height=12
    )

    for col in columns:
        table.heading(col, text=col.replace("_", " ").title())
        table.column(col, width=130, anchor="center")

    table.pack(fill="both", expand=True, padx=10, pady=10)
    return table


def refresh_books(search=""):
    for row in books_table.get_children():
        books_table.delete(row)

    query = """
        SELECT * FROM books
        WHERE title LIKE ? OR author LIKE ?
        OR category LIKE ? OR isbn LIKE ?
        ORDER BY id DESC
    """

    term = f"%{search}%"
    cursor.execute(query, (term, term, term, term))

    for row in cursor.fetchall():
        books_table.insert("", "end", values=row)


def refresh_members():
    for row in members_table.get_children():
        members_table.delete(row)

    cursor.execute("SELECT * FROM members ORDER BY id DESC")

    for row in cursor.fetchall():
        members_table.insert("", "end", values=row)


def refresh_borrowings():
    for row in borrow_table.get_children():
        borrow_table.delete(row)

    cursor.execute("""
        SELECT b.id, books.title, members.name,
               b.borrow_date, b.status
        FROM borrowings b
        JOIN books ON b.book_id = books.id
        JOIN members ON b.member_id = members.id
        ORDER BY b.id DESC
    """)

    for row in cursor.fetchall():
        borrow_table.insert("", "end", values=row)


def get_selected_id(table):
    selected = table.selection()

    if not selected:
        messagebox.showwarning("Selection", "Please select a record.")
        return None

    return table.item(selected[0], "values")[0]


# ==========================================
# 4. BOOK MANAGEMENT
# ==========================================

def add_book():
    title = simpledialog.askstring("Add Book", "Enter book title:")
    if not title:
        return

    author = simpledialog.askstring("Add Book", "Enter author:")
    if not author:
        return

    category = simpledialog.askstring("Add Book", "Enter category:")
    if not category:
        return

    isbn = simpledialog.askstring("Add Book", "Enter ISBN:")
    if not isbn:
        return

    quantity = simpledialog.askinteger(
        "Add Book", "Enter quantity:", minvalue=1
    )

    if quantity is None:
        return

    try:
        cursor.execute("""
            INSERT INTO books (title, author, category, isbn, quantity)
            VALUES (?, ?, ?, ?, ?)
        """, (title, author, category, isbn, quantity))

        conn.commit()
        refresh_books()
        update_dashboard()
        messagebox.showinfo("Success", "Book added successfully!")

    except sqlite3.IntegrityError:
        messagebox.showerror("Error", "This ISBN already exists.")


def delete_book():
    book_id = get_selected_id(books_table)
    if book_id is None:
        return

    cursor.execute("""
        SELECT COUNT(*) FROM borrowings
        WHERE book_id = ? AND status = 'Borrowed'
    """, (book_id,))

    if cursor.fetchone()[0] > 0:
        messagebox.showerror(
            "Error", "This book currently has an active borrowing."
        )
        return

    if messagebox.askyesno("Confirm", "Delete this book?"):
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        refresh_books()
        update_dashboard()


# ==========================================
# 5. MEMBER MANAGEMENT
# ==========================================

def add_member():
    name = simpledialog.askstring("Add Member", "Enter member name:")
    if not name:
        return

    email = simpledialog.askstring("Add Member", "Enter email:")
    if email is None:
        return

    phone = simpledialog.askstring("Add Member", "Enter phone:")
    if phone is None:
        return

    cursor.execute("""
        INSERT INTO members (name, email, phone)
        VALUES (?, ?, ?)
    """, (name, email, phone))

    conn.commit()
    refresh_members()
    update_dashboard()

    messagebox.showinfo("Success", "Member registered successfully!")


def delete_member():
    member_id = get_selected_id(members_table)
    if member_id is None:
        return

    cursor.execute("""
        SELECT COUNT(*) FROM borrowings
        WHERE member_id = ? AND status = 'Borrowed'
    """, (member_id,))

    if cursor.fetchone()[0] > 0:
        messagebox.showerror(
            "Error", "This member has active borrowings."
        )
        return

    if messagebox.askyesno("Confirm", "Delete this member?"):
        cursor.execute("DELETE FROM members WHERE id = ?", (member_id,))
        conn.commit()
        refresh_members()
        update_dashboard()


# ==========================================
# 6. BORROW AND RETURN BOOKS
# ==========================================

def borrow_book():
    book_id = simpledialog.askinteger(
        "Borrow Book", "Enter Book ID:"
    )
    if book_id is None:
        return

    member_id = simpledialog.askinteger(
        "Borrow Book", "Enter Member ID:"
    )
    if member_id is None:
        return

    cursor.execute("SELECT quantity FROM books WHERE id = ?", (book_id,))
    book = cursor.fetchone()

    cursor.execute("SELECT id FROM members WHERE id = ?", (member_id,))
    member = cursor.fetchone()

    if not book or not member:
        messagebox.showerror("Error", "Invalid book or member ID.")
        return

    if book[0] <= 0:
        messagebox.showwarning("Unavailable", "This book is out of stock.")
        return

    cursor.execute("""
        INSERT INTO borrowings
        (book_id, member_id, borrow_date, status)
        VALUES (?, ?, ?, 'Borrowed')
    """, (book_id, member_id, str(date.today())))

    cursor.execute("""
        UPDATE books SET quantity = quantity - 1
        WHERE id = ?
    """, (book_id,))

    conn.commit()

    refresh_books()
    refresh_borrowings()
    update_dashboard()

    messagebox.showinfo("Success", "Book borrowed successfully!")


def return_book():
    borrowing_id = get_selected_id(borrow_table)
    if borrowing_id is None:
        return

    cursor.execute("""
        SELECT book_id, status FROM borrowings WHERE id = ?
    """, (borrowing_id,))

    record = cursor.fetchone()

    if not record or record[1] != "Borrowed":
        messagebox.showwarning("Warning", "This book is already returned.")
        return

    cursor.execute("""
        UPDATE borrowings
        SET status = 'Returned', return_date = ?
        WHERE id = ?
    """, (str(date.today()), borrowing_id))

    cursor.execute("""
        UPDATE books SET quantity = quantity + 1
        WHERE id = ?
    """, (record[0],))

    conn.commit()

    refresh_books()
    refresh_borrowings()
    update_dashboard()

    messagebox.showinfo("Success", "Book returned successfully!")


# ==========================================
# 7. BOOK RECOMMENDATIONS
# ==========================================

def show_recommendations():
    for row in recommendation_table.get_children():
        recommendation_table.delete(row)

    cursor.execute("""
        SELECT books.category, COUNT(borrowings.id) AS total
        FROM borrowings
        JOIN books ON borrowings.book_id = books.id
        GROUP BY books.category
        ORDER BY total DESC
        LIMIT 1
    """)

    result = cursor.fetchone()

    if result:
        category = result[0]
        cursor.execute("""
            SELECT id, title, author, category, quantity
            FROM books
            WHERE category = ? AND quantity > 0
            ORDER BY title
        """, (category,))
        recommendations = cursor.fetchall()
    else:
        cursor.execute("""
            SELECT id, title, author, category, quantity
            FROM books
            WHERE quantity > 0
            ORDER BY id DESC
        """)
        recommendations = cursor.fetchall()

    for book in recommendations:
        recommendation_table.insert("", "end", values=book)

    if not recommendations:
        messagebox.showinfo(
            "Recommendations", "No available books to recommend."
        )


# ==========================================
# 8. DASHBOARD AND STATISTICS
# ==========================================

def update_dashboard():
    cursor.execute("SELECT COUNT(*) FROM books")
    total_books = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(quantity) FROM books")
    available_books = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM members")
    total_members = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM borrowings
        WHERE status = 'Borrowed'
    """)
    active_borrowings = cursor.fetchone()[0]

    stat_books.config(text=str(total_books))
    stat_available.config(text=str(available_books))
    stat_members.config(text=str(total_members))
    stat_borrowed.config(text=str(active_borrowings))

    draw_statistics()


def draw_statistics():
    chart.delete("all")

    cursor.execute("""
        SELECT books.title, COUNT(borrowings.id) AS total
        FROM borrowings
        JOIN books ON borrowings.book_id = books.id
        GROUP BY books.id
        ORDER BY total DESC
        LIMIT 5
    """)

    data = cursor.fetchall()

    chart.create_text(
        350, 20,
        text="TOP BORROWED BOOKS",
        fill=WHITE,
        font=("Arial", 14, "bold")
    )

    if not data:
        chart.create_text(
            350, 100,
            text="No borrowing data available yet.",
            fill=MUTED,
            font=("Arial", 12)
        )
        return

    max_value = max(item[1] for item in data)

    for i, (title, total) in enumerate(data):
        y = 65 + i * 55
        width = (total / max_value) * 400

        chart.create_text(
            15, y + 10,
            text=title[:20],
            anchor="w",
            fill=WHITE,
            font=("Arial", 10)
        )

        chart.create_rectangle(
            180, y, 180 + width, y + 22,
            fill=PURPLE,
            outline=""
        )

        chart.create_text(
            190 + width, y + 10,
            text=str(total),
            fill=WHITE,
            anchor="w"
        )


# ==========================================
# 9. MAIN INTERFACE
# ==========================================

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "TNotebook",
    background=BG,
    borderwidth=0
)

style.configure(
    "TNotebook.Tab",
    background=PANEL,
    foreground=WHITE,
    padding=[18, 10],
    font=("Arial", 10, "bold")
)

style.map(
    "TNotebook.Tab",
    background=[("selected", PURPLE)],
    foreground=[("selected", "white")]
)

style.configure(
    "Treeview",
    background=PANEL,
    foreground=WHITE,
    fieldbackground=PANEL,
    rowheight=30,
    font=("Arial", 10)
)

style.configure(
    "Treeview.Heading",
    background=PURPLE,
    foreground=WHITE,
    font=("Arial", 10, "bold")
)

# Header
header = tk.Frame(root, bg=BG)
header.pack(fill="x", padx=20, pady=15)

tk.Label(
    header,
    text="SMART LIBRARY",
    font=("Arial", 23, "bold"),
    bg=BG,
    fg=WHITE
).pack(side="left")

tk.Label(
    header,
    text="Management System",
    font=("Arial", 11),
    bg=BG,
    fg=MUTED
).pack(side="left", padx=12, pady=8)

# Notebook
notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True, padx=15, pady=10)

dashboard_tab = tk.Frame(notebook, bg=BG)
books_tab = tk.Frame(notebook, bg=BG)
members_tab = tk.Frame(notebook, bg=BG)
borrow_tab = tk.Frame(notebook, bg=BG)
recommendation_tab = tk.Frame(notebook, bg=BG)

notebook.add(dashboard_tab, text="Dashboard")
notebook.add(books_tab, text="Books")
notebook.add(members_tab, text="Members")
notebook.add(borrow_tab, text="Borrow / Return")
notebook.add(recommendation_tab, text="Recommendations")


# ==========================================
# 10. DASHBOARD DESIGN
# ==========================================

tk.Label(
    dashboard_tab,
    text="Library Overview",
    font=("Arial", 19, "bold"),
    bg=BG,
    fg=WHITE
).pack(anchor="w", padx=20, pady=15)

cards = tk.Frame(dashboard_tab, bg=BG)
cards.pack(fill="x", padx=15)

def create_card(parent, title, color):
    frame = tk.Frame(parent, bg=PANEL, padx=15, pady=15)
    frame.pack(side="left", fill="both", expand=True, padx=6)

    tk.Label(
        frame, text=title,
        bg=PANEL, fg=MUTED,
        font=("Arial", 10)
    ).pack(anchor="w")

    value = tk.Label(
        frame, text="0",
        bg=PANEL, fg=color,
        font=("Arial", 25, "bold")
    )
    value.pack(anchor="w", pady=8)

    return value


stat_books = create_card(cards, "Total Titles", PURPLE)
stat_available = create_card(cards, "Available Copies", GREEN)
stat_members = create_card(cards, "Total Members", "#38BDF8")
stat_borrowed = create_card(cards, "Currently Borrowed", "#F59E0B")

chart = tk.Canvas(
    dashboard_tab,
    bg=PANEL,
    height=350,
    highlightthickness=0
)
chart.pack(fill="both", expand=True, padx=20, pady=25)


# ==========================================
# 11. BOOKS TAB
# ==========================================

book_controls = tk.Frame(books_tab, bg=BG)
book_controls.pack(fill="x", padx=10, pady=10)

tk.Button(
    book_controls, text="Add Book",
    bg=PURPLE, fg=WHITE,
    command=add_book
).pack(side="left", padx=5)

tk.Button(
    book_controls, text="Delete Book",
    bg="#DC2626", fg=WHITE,
    command=delete_book
).pack(side="left", padx=5)

search_var = tk.StringVar()

search_entry = tk.Entry(
    book_controls,
    textvariable=search_var,
    width=30,
    font=("Arial", 11)
)
search_entry.pack(side="right", padx=5)

tk.Label(
    book_controls,
    text="Search:",
    bg=BG,
    fg=WHITE
).pack(side="right")

books_table = create_table(
    books_tab,
    ("id", "title", "author", "category", "isbn", "quantity")
)

search_var.trace_add(
    "write",
    lambda *args: refresh_books(search_var.get())
)


# ==========================================
# 12. MEMBERS TAB
# ==========================================

member_controls = tk.Frame(members_tab, bg=BG)
member_controls.pack(fill="x", padx=10, pady=10)

tk.Button(
    member_controls, text="Add Member",
    bg=PURPLE, fg=WHITE,
    command=add_member
).pack(side="left", padx=5)

tk.Button(
    member_controls, text="Delete Member",
    bg="#DC2626", fg=WHITE,
    command=delete_member
).pack(side="left", padx=5)

members_table = create_table(
    members_tab,
    ("id", "name", "email", "phone")
)


# ==========================================
# 13. BORROW / RETURN TAB
# ==========================================

borrow_controls = tk.Frame(borrow_tab, bg=BG)
borrow_controls.pack(fill="x", padx=10, pady=10)

tk.Button(
    borrow_controls, text="Borrow Book",
    bg=PURPLE, fg=WHITE,
    command=borrow_book
).pack(side="left", padx=5)

tk.Button(
    borrow_controls, text="Return Selected Book",
    bg=GREEN, fg=WHITE,
    command=return_book
).pack(side="left", padx=5)

borrow_table = create_table(
    borrow_tab,
    ("id", "title", "member", "borrow_date", "status")
)


# ==========================================
# 14. RECOMMENDATIONS TAB
# ==========================================

tk.Label(
    recommendation_tab,
    text="Recommended Books",
    font=("Arial", 18, "bold"),
    bg=BG,
    fg=WHITE
).pack(anchor="w", padx=15, pady=15)

tk.Label(
    recommendation_tab,
    text="Recommendations are based on popular borrowing categories.",
    bg=BG,
    fg=MUTED
).pack(anchor="w", padx=15)

tk.Button(
    recommendation_tab,
    text="Generate Recommendations",
    bg=PURPLE,
    fg=WHITE,
    command=show_recommendations
).pack(anchor="w", padx=15, pady=15)

recommendation_table = create_table(
    recommendation_tab,
    ("id", "title", "author", "category", "quantity")
)


# ==========================================
# 15. START APPLICATION
# ==========================================

refresh_books()
refresh_members()
refresh_borrowings()
show_recommendations()
update_dashboard()


def close_application():
    conn.close()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_application)

root.mainloop()
