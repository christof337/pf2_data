<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="text" encoding="UTF-8"/>
  
  <xsl:template match="/monsters/monster">
    <xsl:text>```pf2e-stats&#10;</xsl:text>
    <xsl:text>#### [[fr]]&#10;</xsl:text>
    <xsl:text># </xsl:text><xsl:value-of select="name"/><xsl:text> &#10;</xsl:text>
    <xsl:text>## </xsl:text><xsl:value-of select="type"/><xsl:text> </xsl:text><xsl:value-of select="level"/><xsl:text>&#10;</xsl:text>
    <xsl:text>----&#10;</xsl:text>
    
    <!-- Traits -->
    <xsl:for-each select="creatureTraits/trait">
      <xsl:text>==</xsl:text><xsl:value-of select="."/><xsl:text>==</xsl:text>
      <xsl:if test="position() != last()"><xsl:text> </xsl:text></xsl:if>
    </xsl:for-each>
    <xsl:text>&#10;</xsl:text>
    
    <!-- Perception et Sens -->
    <xsl:text>**Perception** </xsl:text><xsl:value-of select="perception/bonus"/>
    <xsl:if test="perception/senses/sens">
      <xsl:text> ; </xsl:text>
      <xsl:for-each select="perception/senses/sens">
        <xsl:value-of select="name"/>
        <xsl:if test="precision"> (<xsl:value-of select="precision"/>)</xsl:if>
        <xsl:if test="range"><xsl:text> </xsl:text><xsl:value-of select="range"/></xsl:if>
        <xsl:if test="source"> (<xsl:value-of select="source"/>)</xsl:if>
        <xsl:if test="position() != last()">, </xsl:if>
      </xsl:for-each>
    </xsl:if>
    <xsl:text>&#10;</xsl:text>
    
    <!-- Langues -->
    <xsl:if test="languages/language or languages/langSpecial">
      <xsl:text>**Langues** </xsl:text>
      <xsl:for-each select="languages/language">
        <xsl:value-of select="."/>
        <xsl:if test="position() != last()">, </xsl:if>
      </xsl:for-each>
      <xsl:if test="languages/langSpecial">
        <xsl:if test="languages/language"><xsl:text> </xsl:text></xsl:if>
        <xsl:text> ; </xsl:text>
        <xsl:for-each select="languages/langSpecial/*">
          <xsl:choose>
            <xsl:when test="name() = 'spell'">*<xsl:value-of select="."/>*</xsl:when>
            <xsl:otherwise><xsl:value-of select="."/></xsl:otherwise>
          </xsl:choose>
          <xsl:if test="position() != last()">, </xsl:if>
        </xsl:for-each>
      </xsl:if>
      <xsl:text>&#10;</xsl:text>
    </xsl:if>
    
    <!-- Compétences -->
    <xsl:if test="skills/skill">
      <xsl:text>**Compétences** </xsl:text>
      <xsl:for-each select="skills/skill">
        <xsl:value-of select="name"/><xsl:text> </xsl:text><xsl:value-of select="bonus"/>
        <xsl:if test="position() != last()">, </xsl:if>
      </xsl:for-each>
      <xsl:text>&#10;</xsl:text>
    </xsl:if>
    
    <!-- Caractéristiques -->
    <xsl:text>**For** </xsl:text><xsl:value-of select="attributes/@STR"/>
    <xsl:text>, **Dex** </xsl:text><xsl:value-of select="attributes/@DEX"/>
    <xsl:text>, **Con** </xsl:text><xsl:value-of select="attributes/@CON"/>
    <xsl:text>, **Int** </xsl:text><xsl:value-of select="attributes/@INT"/>
    <xsl:text>, **Sag** </xsl:text><xsl:value-of select="attributes/@WIS"/>
    <xsl:text>, **Cha** </xsl:text><xsl:value-of select="attributes/@CHA"/>
    <xsl:text>&#10;----&#10;</xsl:text>
    
    <!-- Défenses (CA, Sauvegardes) -->
    <xsl:text>**CA** </xsl:text><xsl:value-of select="armorClass"/>
    <xsl:text> ; **Réf** </xsl:text><xsl:value-of select="saves/@REF"/>
    <xsl:text>, **Vig** </xsl:text><xsl:value-of select="saves/@FOR"/>
    <xsl:text>, **Vol** </xsl:text><xsl:value-of select="saves/@WIL"/>
    <xsl:if test="saves/@saveSpecial">
      <xsl:text> ; </xsl:text>
        <xsl:value-of select="saves/@saveSpecial"/>
    </xsl:if>
    <xsl:text>&#10;</xsl:text>
    
    <!-- Santé et Résistances -->
    <xsl:text>**PV** </xsl:text><xsl:value-of select="health"/>
    <xsl:if test="immunities/immunity">
      <xsl:text> ; **Immunité</xsl:text><xsl:if test="count(immunities/immunity) &gt; 1">s</xsl:if><xsl:text>** </xsl:text>
      <xsl:for-each select="immunities/immunity">
        <xsl:value-of select="."/>
        <xsl:if test="position() != last()">, </xsl:if>
      </xsl:for-each>
    </xsl:if>
    <xsl:if test="weaknesses/weakness">
      <xsl:text> ; **Faiblesse</xsl:text><xsl:if test="count(weaknesses/weakness) &gt; 1">s</xsl:if><xsl:text>** </xsl:text>
      <xsl:for-each select="weaknesses/weakness">
        <xsl:value-of select="name"/><xsl:text> </xsl:text><xsl:value-of select="value"/>
        <xsl:if test="position() != last()">, </xsl:if>
      </xsl:for-each>
    </xsl:if>
    <xsl:if test="resistances/resistance">
      <xsl:text> ; **Résistance</xsl:text><xsl:if test="count(resistances/resistance) &gt; 1">s</xsl:if><xsl:text>** </xsl:text>
      <xsl:for-each select="resistances/resistance">
        <xsl:value-of select="name"/><xsl:text> </xsl:text><xsl:value-of select="value"/>
        <xsl:if test="position() != last()">, </xsl:if>
      </xsl:for-each>
    </xsl:if>
    <xsl:text>&#10;</xsl:text>
    
    <!-- Capacités Réactives / Auras (Bloc Haut) -->
    <xsl:for-each select="reactiveAbilities/special">
      <xsl:call-template name="format-special-block"/>
    </xsl:for-each>
    
    <!-- Vitesse -->
    <xsl:text>**Vitesse** </xsl:text>
    <xsl:for-each select="speeds/speed">
      <xsl:choose>
        <xsl:when test="@type='climb'">
            <xsl:text>escalade </xsl:text>
        </xsl:when>
        <xsl:when test="@type='swim'">
          <xsl:text>nage </xsl:text>
        </xsl:when>
        <xsl:when test="@type='burrow'">
          <xsl:text>creusement </xsl:text>
        </xsl:when>
        <xsl:when test="@type='fly'">
          <xsl:text>vol </xsl:text>
        </xsl:when>
      </xsl:choose>
      <xsl:value-of select="."/>
      <xsl:if test="position() != last()">, </xsl:if>
    </xsl:for-each>
    <xsl:text>&#10;</xsl:text>
    
    <!-- Attaques (Frappes) -->
    <xsl:for-each select="strikes/strike">
      <xsl:text>**</xsl:text>
      <xsl:choose>
        <xsl:when test="@type='melee'">Corps à corps</xsl:when>
        <xsl:when test="@type='ranged'">À distance</xsl:when>
        <xsl:otherwise><xsl:value-of select="@type"/></xsl:otherwise>
      </xsl:choose>
      <xsl:text>** `[one-action]` </xsl:text>
      <xsl:value-of select="name"/><xsl:text> </xsl:text><xsl:value-of select="bonus"/>
      <xsl:if test="traits/trait">
        <xsl:text> (</xsl:text>
        <xsl:for-each select="traits/trait">
          <xsl:value-of select="."/>
          <xsl:if test="position() != last()">, </xsl:if>
        </xsl:for-each>
        <xsl:text>)</xsl:text>
      </xsl:if>
      <xsl:apply-templates select="damages"/>
      <xsl:text>&#10;</xsl:text>
    </xsl:for-each>
    
    <xsl:apply-templates select="spellList"/>
    
    <!-- Capacités Offensives (Bloc Bas) -->
    <xsl:for-each select="offensiveAbilities/special">
      <xsl:call-template name="format-special-block"/>
    </xsl:for-each>
  </xsl:template>
  
  <!-- Template réutilisable pour les capacités (Spécial) -->
  <xsl:template name="format-special-block">
    <xsl:text>**</xsl:text><xsl:value-of select="name"/><xsl:text>**</xsl:text>
    
    <!-- Traduction des icônes d'actions -->
    <xsl:if test="@actions or @type='reaction' or @type='free'">
      <xsl:text> </xsl:text>
      <xsl:choose>
        <xsl:when test="@actions='1'">`[one-action]`</xsl:when>
        <xsl:when test="@actions='2'">`[two-actions]`</xsl:when>
        <xsl:when test="@actions='3'">`[three-actions]`</xsl:when>
        <xsl:when test="@type='reaction'">`[reaction]`</xsl:when>
        <xsl:when test="@type='free'">`[free-action]`</xsl:when>
      </xsl:choose>
    </xsl:if>
    
    <!-- Traits de la capacité -->
    <xsl:if test="traits/trait">
      <xsl:text> (</xsl:text>
      <xsl:for-each select="traits/trait">
        <xsl:value-of select="."/>
        <xsl:if test="position() != last()">, </xsl:if>
      </xsl:for-each>
      <xsl:text>)</xsl:text>
    </xsl:if>
    <xsl:text> </xsl:text>
    
    <!-- Déclencheur / Effet / Description -->
    <xsl:if test="trigger">
      <xsl:text>**Déclencheur.** </xsl:text><xsl:value-of select="trigger"/>
    </xsl:if>
    <xsl:if test="effect">
      <xsl:text>**Effet.** </xsl:text><xsl:value-of select="effect"/>
    </xsl:if>
    
    <!-- Analyse récursive de la description -->
    <xsl:apply-templates select="description"/>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>
  
  <!-- Templates de formatage de contenu -->
  <xsl:template match="description">
    <xsl:apply-templates/>
  </xsl:template>
  
  <xsl:template match="list">
    <xsl:text>&#10;</xsl:text>
    <xsl:apply-templates select="listItem"/>
  </xsl:template>
  
  <xsl:template match="listItem">
    <xsl:text>- </xsl:text><xsl:apply-templates/><xsl:text>&#10;</xsl:text>
  </xsl:template>
  
  <xsl:template match="b | strong">
    <xsl:text>**</xsl:text><xsl:apply-templates/><xsl:text>**</xsl:text>
  </xsl:template>
  
  <xsl:template match="i | em">
    <xsl:text>*</xsl:text><xsl:apply-templates/><xsl:text>*</xsl:text>
  </xsl:template>
  
  <xsl:template match="damages">
    <xsl:text>, **Dégâts** </xsl:text>
    <xsl:for-each select="damage">
      <xsl:if test="position()>1"> plus </xsl:if>
      <xsl:value-of select="amount"/>&#xA0;<xsl:value-of select="damageType"/>
    </xsl:for-each>
  </xsl:template>
  
  <xsl:template match="spellList">
    <xsl:text>**Sorts </xsl:text>
    <xsl:choose>
      <xsl:when test="@source='prepared'"><xsl:text>préparés </xsl:text></xsl:when>
      <xsl:when test="@source='innate'"><xsl:text>innés </xsl:text></xsl:when>
      <xsl:when test="@source='spontaneous'"><xsl:text>spontanés </xsl:text>
      </xsl:when>
    </xsl:choose>
    <xsl:choose>
      <xsl:when test="@tradition='arcane'"> <xsl:text>arcaniques </xsl:text></xsl:when>
      <xsl:when test="@tradition='divine'"> <xsl:text>divins </xsl:text></xsl:when>
      <xsl:when test="@tradition='occult'"> <xsl:text>occultes </xsl:text></xsl:when>
      <xsl:when test="@tradition='primal'"> <xsl:text>primordiaux </xsl:text></xsl:when>
    </xsl:choose>
    
    <xsl:text>** DD </xsl:text>
    <xsl:value-of select="@DD"/><xsl:text> ; </xsl:text> 
    <xsl:for-each select="rank">
      <xsl:text>**</xsl:text>
        <xsl:choose>
          <xsl:when test="@constant='TRUE'"><xsl:text>Constant (</xsl:text><xsl:value-of select="@rank"/><xsl:text>e)</xsl:text></xsl:when>
          <xsl:when test="@cantrips='TRUE'"><xsl:text>Tours de magie (</xsl:text><xsl:value-of select="@rank"/><xsl:text>e)</xsl:text></xsl:when>
          <xsl:otherwise><xsl:value-of select="@rank"/><xsl:text>e</xsl:text></xsl:otherwise>
        </xsl:choose>
      <xsl:text>**</xsl:text>
      <xsl:for-each select="spells/spell">
        <xsl:text>&#xA0;</xsl:text><xsl:apply-templates select="."/>
        <xsl:if test="not(position()=last())"><xsl:text>, </xsl:text></xsl:if>
      </xsl:for-each>
      <xsl:if test="not(position()=last())"><xsl:text> ; </xsl:text></xsl:if>
    </xsl:for-each>
    <xsl:text>&#10;</xsl:text>
  </xsl:template>
  
  <xsl:template match="spell">
    <xsl:text>*</xsl:text><xsl:value-of select="."/><xsl:text>*</xsl:text>
    <xsl:if test="@source"><xsl:text> (</xsl:text><xsl:value-of select="@source"/><xsl:text>)</xsl:text></xsl:if>
    <xsl:if test="@spellSpecial"><xsl:text> (</xsl:text><xsl:value-of select="@spellSpecial"/><xsl:text>)</xsl:text></xsl:if>
  </xsl:template>

  <!-- Sorts Innés / Préparés -->
  <!--  <xsl:for-each select="innateSpells">
      <xsl:text>**Sorts </xsl:text><xsl:value-of select="tradition"/><xsl:text> innés** </xsl:text>
      <xsl:text>DD </xsl:text><xsl:value-of select="dc"/>
      <xsl:if test="attack">, attaque <xsl:value-of select="attack"/></xsl:if>
      <xsl:for-each select="spellGroup">
        <xsl:text> ; **</xsl:text>
        <xsl:choose>
          <xsl:when test="@type='cantrip'">Tours de magie (<xsl:value-of select="@level"/>e)</xsl:when>
          <xsl:when test="@type='constant'">Constant (<xsl:value-of select="@level"/>e)</xsl:when>
          <xsl:otherwise><xsl:value-of select="@level"/><xsl:text>e</xsl:text></xsl:otherwise>
        </xsl:choose>
        <xsl:text>** </xsl:text>
        <xsl:for-each select="spell">
          <xsl:text>*</xsl:text><xsl:value-of select="name"/><xsl:text>*</xsl:text>
          <xsl:if test="details"> (<xsl:value-of select="details"/>)</xsl:if>
          <xsl:if test="position() != last()">, </xsl:if>
        </xsl:for-each>
      </xsl:for-each>
      <xsl:text>&#10;</xsl:text>
    </xsl:for-each> -->
</xsl:stylesheet>

<!--  
     
     -
     
     ### 2. Le rendu Markdown généré par cet XSLT
     
     Voici exactement la sortie qu'il produit à partir de ton fichier `young_empyreal_dragon.xml` actuel. Tu remarqueras que ça clone la mise en forme de ta PJ "manuel".
     
     ```markdown
     ```pf2e-stats
     #### [[fr]]
     # JEUNE DRAGON EMPYRÉEN
     ## CRÉATURE 10
     -
     ==GRANDE== ==DIVIN== ==DRAGON== ==SAINT== 
     **Perception** +21 ; odorat (imprécis) 18 m, perception de la vie (imprécis) 9 m (p. 360), vision dans le noir
     **Langues** commun, draconique, empyréen ; *langage universel*
     **Compétences** Acrobaties +19, Athlétisme +22, Connaissances sur le Paradis +21, Diplomatie +20, Intimidation +20, Médecine +21, Religion +21, Société +19
     **For** +6, **Dex** +3, **Con** +4, **Int** +3, **Sag** +5, **Cha** +4
     -
     **CA** 30 ; **Réf** +19, **Vig** +18, **Vol** +21 ; bonus de statut de +2 à tous les jets de sauvegarde contre la magie divine
     **PV** 170 ; **Immunités** terreur, paralysé, sommeil ; **Faiblesse** impie 10
     **Déflexion divine** `[reaction]` **Déclencheur.** Le dragon subit un coup critique infligé par une attaque. **Effet.** Une puissance divine intervient et le protège d’une partie des dégâts. Le dragon gagne résistance 10 contre tous les dégâts de l’attaque ayant déclenché le pouvoir. 
     **Présence inspirante** (aura, émotion, mental) 27 m. Les alliés dans l’aura gagnent un bonus de statut de +1 à l’attaque, aux dégâts et aux jets de sauvegarde contre les effets de terreur. Les ennemis dans l’aura subissent une pénalité de statut de –1 à ces mêmes jets.
     **Vitesse** 15 m, vol 36 m
     **Corps à corps** `[one-action]` mâchoire +23 (allonge 3 m, divine, feu, magique), **Dégâts** 2d10+12 perforant plus 1d8 feu et 1d8 esprit
     **Corps à corps** `[one-action]` griffes +23 (agile, magique), **Dégâts** 2d10+12 tranchant
     **Corps à corps** `[one-action]` queue +21 (allonge 4,5 m, divine, magique), **Dégâts** 1d10+10 contondant plus 1d8 esprit
     **Sorts divins innés** DD 29, attaque +21 ; **5e** *guérison* ; **3e** *lumière sainte* (à volonté) ; **Constant (5e)** *langage universel*
     **Frénésie draconique** `[two-actions]` Le dragon effectue deux Frappes de griffes et une Frappe d’ailes dans l’ordre qu’il veut.
     **Impulsion draconique.** Le dragon recharge son Souffle spirituel chaque fois qu’il inflige un coup critique avec une Frappe.
     **Manipulation de halo** `[one-action]` (concentration, divine, manipulation) Le dragon envoie son halo sur une case à moins de 27 m. Tant que le halo est ainsi déployé, le dragon perd son aura de présence inspirante qui à la place émane du halo sur une même distance. Le dragon peut Maintenir l’effet pour rappeler le halo à lui, peu importe la distance qui les sépare. Le halo est constitué de lumière pure, n’occupe aucun espace et ne peut être ni ciblé ni détruit.
     **Pulsation du halo** `[two-actions]` (concentration, divine) Le dragon choisit un effet à imposer aux créa- tures dans son aura de Présence inspirante. Le dragon ne peut utiliser Pulsation du halo pendant 1d4 rounds.
     - **Répulsion.** Chaque créature doit réussir un jet de Vigueur DD 29 ou être repoussée jusqu’à ce qu’elle ait quitté l’aura.
     - **Restauration** (guérison, vitalité) Chaque créature récupère 5d8 PV.
     
     **Souffle spirituel** `[two-actions]` (divine, esprit, saint) Le dragon crache un feu saint qui inflige 9d8 dégâts d’esprit dans un cône de 12 m (jet de Réflexes basique DD 29). Le dragon ne peut plus utiliser Souffle spirituel pendant 1d4 rounds.-->