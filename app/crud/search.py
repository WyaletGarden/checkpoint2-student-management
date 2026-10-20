from sqlalchemy import or_


def search_query(query, model, term: str | None):
    """Apply the same literal substring search to lists and their total counts."""
    if not term or not term.strip():
        return query
    fields = {
        "students": ("student_code", "email"),
        "teachers": ("teacher_code", "email"),
        "classes": ("class_code", "class_name"),
    }[model.__tablename__]
    columns = [getattr(model, name) for name in fields]
    if hasattr(model, "last_name"):
        columns.extend([model.last_name, model.first_name,
                        model.last_name + " " + model.first_name])
    return query.filter(or_(*(column.icontains(term.strip(), autoescape=True) for column in columns)))
