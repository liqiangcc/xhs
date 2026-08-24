window.value = "v";

function fnA() {
  console.log(this.value);
}

function fnB() {
  const arrowFn = () => {
    console.log(this.value);
  };
  arrowFn();
}

function fnC() {
  const arrowFn = () => {
    console.log(this.value);
  };
  return arrowFn;
}

const objA = {
  value: "A",
  fn: fnA,
};

const objB = {
  value: "B",
  fn: fnB,
};

const objC = {
  value: "C",
  fn: fnC(),
};

objA.fn();
objB.fn();
objC.fn();
