
    (component
        (import "i" (instance $i
          (export "f1" (func))
          (export "f2" (func))
        ))

        (core func $f1 (canon lower (func $i "f1")))
        (core func $f2 (canon lower (func $i "f2")))

        (func $f1' (canon lift (core func $f1)))
        (func $f2' (canon lift (core func $f2)))

        (instance (export "i1")
            (export "f1" (func $f1')))
        ;;(export "i2" (instance (export "f2" (func $f2))))
    )
