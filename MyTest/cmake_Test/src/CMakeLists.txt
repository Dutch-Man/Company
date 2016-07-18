aux_source_directory(. src_list)
include_directories(${top_dir}/include)
add_executable(Test ${src_list})
