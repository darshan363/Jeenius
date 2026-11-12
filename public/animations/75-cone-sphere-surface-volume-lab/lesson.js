
window.JEENIUS_LESSON = {
  num: 75,
  slug: "cone-sphere-surface-volume-lab",
  title: "Cone and Sphere Lab",
  short: "Surface Area and Volume: Cones and Spheres",
  grade: "CLASS 9",
  subject: "MATHEMATICS",
  chapter: "Surface Area and Volume",
  intro: "Choose a solid and adjust its dimensions.",
  kind: "surface-cone-sphere",

  controls: [
    {
      key: "shape",
      label: "Solid",
      type: "select",
      options: ["Cone", "Sphere"],
      value: 0
    },
    {
      key: "radius",
      label: "Radius",
      min: 1,
      max: 8,
      step: 1,
      value: 3,
      unit: " cm"
    },
    {
      key: "height",
      label: "Vertical height (cone)",
      min: 2,
      max: 12,
      step: 1,
      value: 4,
      unit: " cm"
    }
  ]
};

window.JEENIUS_LESSON.draw = function(c, s, t, h, m) {
  const { N, B, G, W, RED, H, L, R, C, TXT } = h;

  function headline(title, subtitle) {
    H(c, title, 28, 30, 16, "left", "Goldman");
    H(c, subtitle, 28, 51, 11, "left", "Saira", "#52667d");
    L(c, 28, 67, 772, 67, 1, N);
  }

  headline(
    "SURFACE AREA AND VOLUME",
    s.shape === 0 ? "Cone" : "Sphere"
  );

  if (s.shape === 0) {
    // CONE
    const r = s.radius;
    const height = s.height;
    const scale = Math.min(22, 170 / Math.max(r, height));

    const cx = 275;
    const baseY = 333;
    const apexY = baseY - height * scale;
    const rx = r * scale;
    const ry = rx * 0.28;

    R(c, 70, 103, 410, 279, W, N, 1.5);

    // Draw cone
    c.save();
    c.beginPath();
    c.moveTo(cx, apexY);
    c.lineTo(cx - rx, baseY);
    c.ellipse(
      cx, baseY, rx, ry, 0, Math.PI, Math.PI * 2
    );
    c.closePath();

    c.fillStyle = B;
    c.fill();
    c.strokeStyle = N;
    c.lineWidth = 2;
    c.stroke();
    c.restore();

    // Height, radius and slant height
    L(c, cx, apexY, cx, baseY, 1.5, N, [5, 4]);
    L(c, cx, baseY, cx + rx, baseY, 1.5, G);
    L(c, cx, apexY, cx + rx, baseY, 2, RED);

    const slant = Math.sqrt(r * r + height * height);

    H(
      c,
      "h = " + height + " cm",
      cx + 10,
      (apexY + baseY) / 2,
      12
    );

    H(
      c,
      "r = " + r + " cm",
      cx + rx / 2,
      baseY + 24,
      12,
      "center"
    );

    H(
      c,
      "l = " + Number(slant.toFixed(2)) + " cm",
      cx + rx / 2 + 10,
      (apexY + baseY) / 2 + 15,
      11,
      "left",
      "Saira",
      RED
    );

    H(c, "Cone", 275, 388, 13, "center", "Goldman");

    // Cone formulas
    R(c, 514, 105, 250, 278, B, N, 1.5);
    H(c, "CONE FORMULAS", 534, 136, 13, "left", "Goldman");

    TXT(
      c,
      [
        "Slant height: l = √(r² + h²)",
        "Curved area: πrl",
        "Total area: πr(l + r)",
        "Volume: ⅓πr²h"
      ],
      534, 176, 213, 12, 25
    );

  } else {
    // SPHERE
    const r = s.radius;
    const rad = Math.min(115, r * 25);
    const cx = 275;
    const cy = 236;

    R(c, 70, 103, 410, 279, W, N, 1.5);

    C(c, cx, cy, rad, B, N, 2);

    // Sphere guide curves
    for (let i = 0; i < 5; i++) {
      c.save();
      c.beginPath();

      c.ellipse(
        cx,
        cy,
        rad,
        rad * (0.25 + i * 0.12),
        0, 0, Math.PI * 2
      );

      c.strokeStyle = i % 2 ? G : N;
      c.lineWidth = 1;
      c.stroke();
      c.restore();
    }

    // Radius
    L(c, cx, cy, cx + rad, cy, 2, RED);
    C(c, cx, cy, 3, N, N);

    H(
      c,
      "r = " + r + " cm",
      cx + rad / 2,
      cy - 10,
      12,
      "center",
      "Goldman"
    );

    H(c, "Sphere", 275, 388, 13, "center", "Goldman");

    // Sphere formulas
    R(c, 514, 105, 250, 278, B, N, 1.5);
    H(c, "SPHERE FORMULAS", 534, 136, 13, "left", "Goldman");

    TXT(
      c,
      [
        "Surface area: 4πr²",
        "Volume: ⁴⁄₃πr³",
        "Only the radius is needed."
      ],
      534, 176, 213, 25
    );
  }
};
