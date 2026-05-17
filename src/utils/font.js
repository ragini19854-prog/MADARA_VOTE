const MAP = {
  a:'α', b:'b', c:'c', d:'∂', e:'є', f:'f', g:'g', h:'ɦ', i:'ι', j:'j',
  k:'κ', l:'ℓ', m:'ɱ', n:'η', o:'σ', p:'ρ', q:'q', r:'я', s:'s', t:'τ',
  u:'υ', v:'v', w:'ω', x:'x', y:'ყ', z:'z',
  A:'Α', B:'B', C:'C', D:'∂', E:'Є', F:'F', G:'G', H:'H', I:'I', J:'J',
  K:'K', L:'L', M:'M', N:'N', O:'O', P:'P', Q:'Q', R:'R', S:'S', T:'T',
  U:'U', V:'V', W:'W', X:'X', Y:'Y', Z:'Z',
};

function ff(str) {
  return String(str).split('').map(c => MAP[c] || c).join('');
}

module.exports = { ff };
