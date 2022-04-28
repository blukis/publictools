<?php
//
// Database interface class - https://github.com/blukis/blorm/
//
class Blorm {

	public $conn;
	
	// $opts e.g. = ["host"=>'host1', "username"=>'user1', "password"=>'pass1', "database"=>'db1']
	// - If values not provided, will attempt to lookup values by calling global env() 
	//   function (which is assumed to exist) with keys "DB_HOST", "DB_USERNAME", ...
	// - "DB_" prefix can be overriden by passing $opts = {"env_prefix": "NEWPREFIX_"}.
	function __construct($opts=null) {
		$opts = $opts ? $opts : [];
		$prefix = $opts["env_prefix"] ? $opts["env_prefix"] : "DB_";
		// Get values from $opts, or alternately env() lookup.
		$this->db_server = $opts["host"] ? $opts["host"] : env($prefix . "HOST");
		$this->db_user = $opts["username"] ? $opts["username"] : env($prefix . "USERNAME");
		$this->db_pass = $opts["password"] ? $opts["password"] : env($prefix . "PASSWORD");
		$this->db_dbname = $opts["database"] ? $opts["database"] : env($prefix . "DATABASE");
	}

	public static function create($opts=false) {
		$db = new GuDatabase($opts);
		return $db;
	}


	// Connectivity
	//--------------------------
	public function open() {
		$this->conn = new mysqli($this->db_server, $this->db_user, $this->db_pass, $this->db_dbname);

		// Check for connectivity Errors
		$errorCode = $this->conn->connect_errno;
		if ($errorCode) {
			throw new Exception("DB connect error: " . $errorCode);
		}
		return $this;
	}

	public function close() { // Disconnect from DB.
		$this->conn->close();
	}


	// Send queries & get results
	//--------------------------
	// "Execute" query only, with no return value.  Error if execution fails.
	public function exec($sql) {
		$result = $this->conn->query($sql);
		if (!$result) throw new Exception("DB-query-error: " . $this->conn->error);
	}

	// Run a sql query, return resulting rows (array of accociative arrays).
	public function results($sql, $max_rows) {
		if (empty($max_rows)) {
			throw new Exception("DB-Error: max_rows not specified.");
		}

		$result = $this->conn->query($sql);
		// Display error and halt if error.
		if (!$result) { throw new Exception("DB-query-error: " . $this->conn->error); }

		$row_array = array();
		
		$row_index = 0;
		while ($row_index < $max_rows && $row = $result->fetch_array(MYSQLI_ASSOC)) {
			$row_index++;
			array_push($row_array, $row);
		}
		
		$result->close();
		return $row_array;
	}

	// First result row only, or (null) if no rows returned.
	public function firstRowOrNull($sql) {
		$rows = $this->queryResults($sql, 1);
		return sizeof($rows) ? $rows[0] : null;
	}
	// First result row only. (Errors if no rows returned.)
	public function firstRow($sql) {
		$row = firstRowOrNull($sql);
		if (is_null($row)) throw new Exception("No rows returned, in firstRow().");
		return $row;
	}

	// First cell of first row only. (Errors if no rows returned.)
	public function firstCell($sql) {
		$result = $this->conn->query($sql);
		if (!$result) throw new Exception("DB firstCell error: '" . $this->conn->error . "'");

		$row = $result->fetch_array(MYSQLI_NUM);
		$result->close();
		return $row[0];
	}
	// First cell of first row only, or $errorVal if no rows are returned.
	public function firstCellOrVal($sql, $noRowsVal) {
		$row = $this->firstRowOrNull($sql);
		return $row ? $row[0] : $noRowsVal;
	}


	// Misc util
	//-----------------
	public function lastInsertId() {
		$id = $this->conn->insert_id;
		if (!$id) throw new Exception("DB lastInsertId error: '" . $this->conn->error . "'");
		return $id;
	}
	public function affectedRows() {
		return $this->conn->affected_rows;
	}


	// Converting values to SQL expressions of various types, for use in SQL queries.
	//-----------------
	public function str($input) {
		// Assumes $input is unescaped string.
		return "'" . $this->conn->real_escape_string($input) . "'";
	}
	public function num($input) {
		if (is_numeric($input) && $input . "" != "") {
			// Note: if input is a string and passes is_numeric, the string is returned
			// unaltered as SQL numeric expression.  Some odd strings can pass 
			// is_numeric (" 123 ", "1337e0"), but they all appear to be valid numeric
			// expressions in Mysql also.
			return $input;
		} elseif (is_null($input)) {
			return "NULL";
		} else {
			throw new Exception("Error converting value to number ('" . $input . "').");
		}	
	}
	public function bit($input) {
		if ($input === true || $input === 1) {
			return "1";
		} elseif ($input === false || $input === 0) {
			return "0";
		} else {
			throw new Exception("Error converting value to bit.");
		}	
	}

	// Convert string array to SQL list expression, with proper string-escaping. ["str1", "str2"] => "('string1', 'string2')"
	// - Useful for SQL 'IN' operator.
	public function strList($inputStrs) {
		$str_callable = array($this, 'str'); // Format for array_map() to call a member.  (https://www.php.net/manual/en/language.types.callable.php)
		return "(" . implode(", ", array_map($str_callable, $inputStrs)) . ")";
	}

	// Convert array of numbers to SQL list expression. [1, 1.2] => "(1, 1.2)"
	// - Useful for SQL 'IN' operator.
	public function numList($inputNums) {
		// Require input is valid inputs for num() (a numeric or null).
		foreach ($inputNums as $num) {
			if (!is_numeric($num) && !is_null($num)) { throw new Exception("Element is given to numList() is not a number."); }
		}
		$num_callable = array($this, 'num'); // Format for array_map() to call a member.  (https://www.php.net/manual/en/language.types.callable.php)
		return "(" . implode(", ", array_map($num_callable, $inputNums)) . ")";
	}

}
?>
