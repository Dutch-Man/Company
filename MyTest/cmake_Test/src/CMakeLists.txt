set(targetName Test)
aux_source_directory(. src_list)
include_directories(${top_dir}/include ${lib_dir}/Clib/include)
add_executable(${targetName} ${src_list})
link_libraries(${tartgetName} Clib)
