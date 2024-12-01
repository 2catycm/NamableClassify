str=$0 # 脚本的文件路径
path=$(dirname $str) 
cd $path || exit

cp -r namable_classify/* ../../namable_classify