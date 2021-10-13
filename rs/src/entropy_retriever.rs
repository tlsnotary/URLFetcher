use nsm_io::Request;
use nsm_io::Response;

fn main() {
    let nsm_fd = nsm_driver::nsm_init();
    let request = Request::GetRandom;
    let response = nsm_driver::nsm_process_request(nsm_fd, request);
    let mut random = vec![];
    if let Response::GetRandom{random: rnd} = response {
        random = rnd;
    }
    println!("{:?}", random);
    nsm_driver::nsm_exit(nsm_fd);
}