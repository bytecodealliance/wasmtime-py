use std::arch::wasm32::unreachable;
use wasi::*;

wit_bindgen_guest_rust::generate!("../python.wit");

#[no_mangle]
pub extern "C" fn environ_get(environ: *mut *mut u8, environ_buf: *mut u8) -> Errno {
    drop((environ, environ_buf));
    ERRNO_SUCCESS
}

#[no_mangle]
pub extern "C" fn environ_sizes_get(environc: *mut Size, environ_buf_size: *mut Size) -> Errno {
    unsafe {
        *environc = 0;
        *environ_buf_size = 0;
    }
    ERRNO_SUCCESS
}

#[no_mangle]
pub extern "C" fn fd_write(
    fd: Fd,
    mut iovs_ptr: *const Ciovec,
    mut iovs_len: usize,
    nwritten: *mut Size,
) -> Errno {
    if fd != 1 && fd != 2 {
        unreachable();
    }
    unsafe {
        // Advance to the first non-empty buffer.
        while iovs_len != 0 && (*iovs_ptr).buf_len == 0 {
            iovs_ptr = iovs_ptr.add(1);
            iovs_len -= 1;
        }
        if iovs_len == 0 {
            *nwritten = 0;
            return ERRNO_SUCCESS;
        }

        let ptr = (*iovs_ptr).buf;
        let len = (*iovs_ptr).buf_len;

        let slice = core::slice::from_raw_parts(ptr, len);
        if fd == 1 {
            python::print(slice);
        } else {
            python::eprint(slice);
        }

        *nwritten = len;
    }
    ERRNO_SUCCESS
}

// Not exactly random but this is just a placeholder until there's a more
// official preview1 adapter.
#[no_mangle]
pub unsafe extern "C" fn random_get(buf: *mut u8, buf_len: Size) -> Errno {
    for i in 0..buf_len {
        *buf.add(i) = 1;
    }

    ERRNO_SUCCESS
}

#[no_mangle]
pub extern "C" fn proc_exit(rval: Exitcode) -> ! {
    drop(rval);
    unreachable() // TODO
}
