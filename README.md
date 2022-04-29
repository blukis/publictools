# Blorm
A small, elegant MySQL database interface for PHP.

## Usage

### Opening a connection
```php
require_once 'Blorm.php';

// Connect to database.
$opts = [
  "host" => 'MYSQL_HOSTNAME',
  "username" => 'MYSQL_USERNAME',
  "password" => 'MYSQL_PASSWORD',
  "database" => 'MYSQL_DATABASE_NAME'
];
$db = Blorm::create($opts)->open();
// (Alternatively, omit $opts param, and create() will attempt to gather these values by calling 
// global env("DB_HOST"), env("DB_USERNAME"), etc.  Note: for this alternate method, env() is not a 
// built-in function, and will have to be made to exist.)

// ...
// DO DATABASE THINGS...
// ...

// Can close connection with $db->close() if desired, but it's not required.
```

### Sending Queries; Getting Results
```php
// Executing a quert (INSERT or UPDATE), with no return results.
//-----------------------

$db->queryExec("INSERT INTO table1 (field1, field2) VALUES 'value1', 'value2')");

// Returning results
//-----------------------

// Get results from database from a query.
$sql = "SELECT field1, field2 FROM table1;";
$max_rows = 1000; // Must provide a maximum result count to return.
$rows = $db->queryResults($sql, $max_rows);

// Loop through all results and do stuff with rows...
foreach ($rows as $row) {
   echo("<div>" . $row["field1"] . ", " . $row["field2"] . "</div>");
}

// Shortcut query methods for returning just the first cell (i.e. the first field of first row)...
//-----------------------

// First cell (only) of first row. (Note: will error if query returns no rows.)
$field1Val = $db->firstCell("SELECT field1 FROM table1 WHERE idField = 6;");

// Like firstCell(), but returns $noRowsVal when result has no rows...
$field1Val = $db->firstCellOrVal($sql, $noRowsVal);
```

### Always prevent SQL-Injection!
```php
// Of course, when constructing queries with variables, never ever do this!  SQL-injection is BAD!
$rows = $db->queryExec("UPDATE table1 SET " .
        "stringField1 = '" . $stringVal1 . "', " . // <--- THIS IS BAD!!!
        "numField1 = " . $numVal1 . ", " .         // <--- THIS IS BAD!!!
        "bitField1 = " . $bitVal1 . ", " .         // <--- THIS IS BAD!!!
    "WHERE idField = " . $idVal1 . ";"             // <--- THIS IS BAD!!!
);

// Instead, always use str(), num(), & bit() SQL-expression functions, like this:
// - Note str() returns a SQL string expression, which includes surrounding quotes.  It also takes care of special-character-escaping.
$sql = "UPDATE table1 SET " .
        "stringField1 = " . $db->str($stringVal1) . ", " . // <-- Good!
        "numField1 = " . $db->num($numVal1) . ", " .       // <-- Good!
        "bitField1 = " . $db->bit($bitVal1) . " " .        // <-- Good!
    "WHERE idField = " . $db->num($idVal1) . ";";          // <-- Good!
$rows = $db->queryExec($sql);

// For list expressions, e.g. for IN clauses, use strList() & numList()
// - Note strList() takes care of string escaping for each element, and numList() enforces each element is numeric.
$str_array = ["asdf", "asd'f", "asdf\"]; // # strList() converts to -> "('asdf', 'asd\'f', 'asdf\\')"
$num_array = [5, 6, 7.0];                // # numList() converts to -> "(5, 6, 7.0)"
$db->queryResults("SELECT field1, field2 FROM table1 WHERE
    field3 IN " . $db->strList($str_array) . " AND
    field4 IN " . $db->numList($num_array) . ";");
```

### Misc
```php
// Getting back auto-incrementing ID value...
$db->queryExec("INSERT INTO table1 (field1, field2) VALUES 'value1', 'value2')");
$lastId = $db->lastInsertId();

// Count affected rows...
$db->queryExec("UPDATE table1 SET field1 = 'newthing' WHERE field1 = 'oldthing');");
$affectedRows = $db->affectedRows();
```
