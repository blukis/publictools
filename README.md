# blorm
Pure, clean php database interface for php

## Usage

### Connectivity:
```php
// Connect to database.
$opts = [
  "host" => 'MYSQL_HOSTNAME',
  "username" => 'MYSQL_USERNAME',
  "password" => 'MYSQL_PASSWORD',
  "database" => 'MYSQL_DATABASE_NAME'
];
$db = Blorm::create($opts)->open();

// Alternatively, omit $opts param, and Blorm will attempt to gather these values by calling 
// global env("DB_HOST"), env("DB_USERNAME"), etc.  Note: for this method, env() is not a 
// built-in function, and will have to be made to exist.

// DO DATABASE STUFF...

// Can close with $db->close() if desired, but not necessary.
```
