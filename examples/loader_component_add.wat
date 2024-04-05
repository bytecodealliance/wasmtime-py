(component
  (core module $C
    (func (export "add") (param i32 i32) (result i32)
      local.get 0
      local.get 1
      i32.add)
  )
  (core instance $c (instantiate $C))
  (core func $add (alias core export $c "add"))
  (func (export "add") (param "x" s32) (param "y" s32) (result s32)
    (canon lift (core func $add)))
)
