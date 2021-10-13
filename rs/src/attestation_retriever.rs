use nsm_io::Request;
use nsm_io::Response;

use serde_bytes::ByteBuf;

use std::fs::File;
use std::io::prelude::*;
use std::path::Path;

fn main() {
    let user_data_path = std::env::args().nth(1).expect("no user_data_path given");
    let out_path = std::env::args().nth(2).expect("no outpath given");
    let path = Path::new(&out_path);
    let display = path.display();

    // Open a file in write-only mode, returns `io::Result<File>`
    let mut file = match File::create(&path) {
        Err(why) => panic!("couldn't create {}: {}", display, why),
        Ok(file) => file,
    };

    let nsm_fd = nsm_driver::nsm_init();

    let user_data = std::fs::read(user_data_path).unwrap();
    let user_data_bytes = ByteBuf::from(user_data);
    let request = Request::Attestation {
        public_key: None,
        user_data: Some(user_data_bytes),
        nonce: None,
    };

    let response = nsm_driver::nsm_process_request(nsm_fd, request);
    let mut attest_doc = vec![];
    if let Response::Attestation{document: docu} = response {
        attest_doc = docu;
    }

    match file.write_all(&attest_doc) {
        Err(why) => panic!("couldn't write to {}: {}", display, why),
        Ok(_) => println!("successfully wrote to {}", display),
    }

    nsm_driver::nsm_exit(nsm_fd);
}