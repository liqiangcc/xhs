package treebuild

import (
  "fmt"
  "math/rand"
  "reflect"
  "testing"
)

type modelNode struct { v int; left,right *modelNode }
func model(vals []*int)(*modelNode,bool){
  if len(vals)==0{return nil,true}
  if vals[0]==nil { for _,v:=range vals[1:] { if v!=nil{return nil,false} }; return nil,true }
  root:=&modelNode{v:*vals[0]}; parents:=[]*modelNode{root}; pos:=1
  for len(parents)>0 && pos<len(vals) {
    p:=parents[0]; parents=parents[1:]
    if pos<len(vals) { if vals[pos]!=nil { p.left=&modelNode{v:*vals[pos]}; parents=append(parents,p.left) }; pos++ }
    if pos<len(vals) { if vals[pos]!=nil { p.right=&modelNode{v:*vals[pos]}; parents=append(parents,p.right) }; pos++ }
  }
  for ;pos<len(vals);pos++ { if vals[pos]!=nil{return nil,false} }
  return root,true
}
func modelLevels(root *modelNode)[][]int { out:=[][]int{}; var walk func(*modelNode,int); walk=func(n *modelNode,d int){if n==nil{return};for len(out)<=d{out=append(out,[]int{})};out[d]=append(out[d],n.v);walk(n.left,d+1);walk(n.right,d+1)};walk(root,0);return out }
func ip(v int)*int{x:=v;return &x}
func check(vals []*int,label string,t *testing.T){
  m,valid:=model(vals); got,err:=BuildLevelOrder(vals)
  if valid!=(err==nil){t.Fatalf("%s validity mismatch valid=%v err=%v",label,valid,err)}
  if !valid{return}
  want:=modelLevels(m); actual:=LevelOrder(got); if !reflect.DeepEqual(actual,want){t.Fatalf("%s got=%v want=%v",label,actual,want)}
}
func enumerate(a []*int,pos int,count *int,t *testing.T){ if pos==len(a){*count++;check(a,"exhaustive",t);return}; options:=[]*int{nil,ip(-1),ip(0),ip(1)};for _,v:=range options{a[pos]=v;enumerate(a,pos+1,count,t)} }
func TestReviewer(t *testing.T){
 fixed:=[][]*int{{},{nil},{nil,nil},{nil,ip(1)},{ip(1)},{ip(1),ip(2),ip(3),nil,ip(4),nil,ip(5)},{ip(1),nil,nil,ip(2)},{ip(1),ip(2),nil,ip(3)},{ip(7),ip(7),ip(7)},{ip(1),nil,ip(2),ip(3),nil,nil,ip(4)}}
 for i,v:=range fixed{check(v,fmt.Sprintf("fixed-%d",i),t)}
 count:=0;for n:=0;n<=6;n++{enumerate(make([]*int,n),0,&count,t)};if count!=5461{t.Fatalf("count=%d",count)}
 r:=rand.New(rand.NewSource(0x6200BC3F));opts:=[]*int{nil,ip(-3),ip(-2),ip(-1),ip(0),ip(1),ip(2),ip(3)};for i:=0;i<30000;i++{n:=r.Intn(24);a:=make([]*int,n);for j:=range a{v:=opts[r.Intn(len(opts))];if v!=nil{x:=*v;a[j]=&x}};check(a,"random",t)}
 fmt.Println("PASS reviewer fixed=10 exhaustive=5461 random=30000 oracle=independent-model invalid_unreachable=pass nil_slots=pass levels=pass")
}
