(module
    (import "wasi_snapshot_preview1" "random_get" (func $random_get (param i32 i32) (result i32)))
    (memory 1)
    (export "memory" (memory 0))
    (func $wasi_random (export "wasi_random")
      (result i32)
      (call $random_get
        (i32.const 0) ;; buffer start position
	(i32.const 1)) ;; buffer length 1 bytes
      ;; this bounds our random between 0-255
      drop ;; random_get returns an error code
      (i32.const 0)
      i32.load))
